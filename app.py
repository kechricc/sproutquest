"""SproutQuest — Flask backend.

A kid-friendly multiplayer plant scavenger hunt:
  - shared-password login (one password for everyone)
  - a host creates a timed hunt and gets a 6-char join code; others join with it
  - players photograph plants -> Plant.id v3 identifies them (>= 95% confidence)
  - live leaderboard + first-finder 2x bonus, pushed over SocketIO
  - hunts auto-end when the timer expires (server is the timekeeping authority)

All secrets come from environment variables (see .env.example). Run locally with
`python app.py`; deploy on Railway with the included Procfile.
"""

import base64
import binascii
import os
import random
import string
from datetime import datetime
from functools import wraps  # noqa: F401  (kept for future per-route decorators)
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_from_directory, session
from flask_socketio import SocketIO, emit, join_room  # noqa: F401

from models import Find, Hunt, Player, db
from plant_catalog import get_plant_info

# Load .env from beside this file, so the app works no matter the working directory.
# (On Railway there's no .env — env vars come from the platform — and this is a no-op.)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --------------------------------------------------------------------------- #
# Configuration (all from the environment)                                    #
# --------------------------------------------------------------------------- #
PLANTID_API_KEY = os.environ.get("PLANTID_API_KEY", "")
SPROUTQUEST_PASSWORD = os.environ.get("SPROUTQUEST_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")
PLANTID_API_URL = os.environ.get("PLANTID_API_URL", "https://api.plant.id/v3/identification")
DATABASE_PATH = os.environ.get("DATABASE_PATH") or str(BASE_DIR / "sproutquest.db")
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

# Minimum species confidence to accept a find (your spec: 95%). Tunable via env —
# 0.95 is strict, so lower it (e.g. 0.8) if real-world kid photos miss too often.
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.95"))
CODE_ALPHABET = string.ascii_uppercase + string.digits
CODE_LENGTH = 6
VALID_DURATIONS = (15, 30, 45, 60)

# Fail fast in production if the session secret is missing; allow a dev fallback.
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-secret-key"
        print("[sproutquest] WARNING: SECRET_KEY not set — using an insecure dev key.")
    else:
        raise RuntimeError("SECRET_KEY environment variable is required in production.")

if not SPROUTQUEST_PASSWORD:
    print("[sproutquest] WARNING: SPROUTQUEST_PASSWORD not set — nobody can log in.")
if not PLANTID_API_KEY:
    print("[sproutquest] WARNING: PLANTID_API_KEY not set — /api/identify will return 503.")

# --------------------------------------------------------------------------- #
# App + extensions                                                            #
# --------------------------------------------------------------------------- #
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(DATABASE_PATH).as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# SQLite + threads: the auto-end timer runs in a background thread, so allow the
# connection to be used across threads. Fine for this app's low write volume.
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"check_same_thread": False}}

db.init_app(app)
# Threading async mode — no eventlet/gevent monkey-patching, behaves the same on
# Windows and Railway. WebSocket is used when available (simple-websocket), else
# Socket.IO falls back to HTTP long-polling. Single worker, so no message queue is
# needed (add message_queue="redis://..." here to scale to multiple workers).
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

with app.app_context():
    db.create_all()


# --------------------------------------------------------------------------- #
# Auth                                                                        #
# --------------------------------------------------------------------------- #
PUBLIC_PATHS = {"/", "/ping", "/auth/login"}


def _ensure_session_id():
    """A stable per-browser id used to tie session -> Player rows."""
    if "sid" not in session:
        session["sid"] = os.urandom(16).hex()
    return session["sid"]


@app.before_request
def require_login():
    path = request.path
    if path in PUBLIC_PATHS or path.startswith("/static") or path.startswith("/socket.io"):
        return None
    if session.get("authed"):
        return None
    if path.startswith("/api"):
        return jsonify({"success": False, "error": "unauthorized"}), 401
    return redirect("/")


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    password = (data.get("password") or "").strip()
    if SPROUTQUEST_PASSWORD and password == SPROUTQUEST_PASSWORD:
        session["authed"] = True
        _ensure_session_id()
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "error": "Wrong password"}), 401


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def _generate_code():
    """A unique 6-char uppercase join code."""
    while True:
        code = "".join(random.choices(CODE_ALPHABET, k=CODE_LENGTH))
        if not db.session.get(Hunt, code):
            return code


def _current_player(hunt_id=None):
    """The Player owned by this browser session (optionally constrained to a hunt)."""
    pid = session.get("player_id")
    if not pid:
        return None
    player = db.session.get(Player, pid)
    if player and (hunt_id is None or player.hunt_id == hunt_id):
        return player
    return None


def _finds_count_by_player(hunt_id):
    rows = (
        db.session.query(Find.player_id, db.func.count(Find.id))
        .filter(Find.hunt_id == hunt_id)
        .group_by(Find.player_id)
        .all()
    )
    return {player_id: count for player_id, count in rows}


def _leaderboard(hunt_id):
    """Players sorted by score desc, then earliest joiner first."""
    players = Player.query.filter_by(hunt_id=hunt_id).all()
    counts = _finds_count_by_player(hunt_id)
    ranked = sorted(players, key=lambda p: (-(p.score or 0), p.joined_at or datetime.utcnow()))
    return [
        {
            "player_id": p.id,
            "name": p.name,
            "score": p.score or 0,
            "finds": counts.get(p.id, 0),
            "rank": i + 1,
        }
        for i, p in enumerate(ranked)
    ]


def _notable_finds(hunt_id):
    """First-discovery finds, newest first, with the finder's name and emoji."""
    firsts = (
        Find.query.filter_by(hunt_id=hunt_id, is_first=True)
        .order_by(Find.found_at.desc())
        .all()
    )
    out = []
    for f in firsts:
        finder = db.session.get(Player, f.player_id)
        info = get_plant_info(f.scientific, f.plant_name)
        out.append(
            {
                "plant_name": f.plant_name,
                "scientific_name": f.scientific,
                "finder_name": finder.name if finder else "Someone",
                "emoji": info["emoji"],
                "points": f.points,
                "found_at": (f.found_at.isoformat() + "Z") if f.found_at else None,
            }
        )
    return out


def _time_remaining(hunt):
    if hunt.status == "ended":
        return 0
    if hunt.status != "active" or not hunt.started_at:
        return hunt.duration * 60  # not started yet
    elapsed = (datetime.utcnow() - hunt.started_at).total_seconds()
    return max(0, int(hunt.duration * 60 - elapsed))


def _end_hunt(hunt):
    """Mark a hunt ended and broadcast the final leaderboard (idempotent)."""
    if hunt.status == "ended":
        return
    hunt.status = "ended"
    hunt.ended_at = datetime.utcnow()
    db.session.commit()
    socketio.emit("hunt_ended", {"final_leaderboard": _leaderboard(hunt.id)}, room=hunt.id)


def _maybe_end_hunt(hunt):
    """Flip an expired active hunt to ended (fallback to the background timer)."""
    if hunt.status == "active" and _time_remaining(hunt) <= 0:
        _end_hunt(hunt)
        return True
    return False


def _schedule_auto_end(hunt_id, duration_minutes):
    """Background greenlet: end the hunt when its timer runs out."""
    socketio.sleep(duration_minutes * 60)
    with app.app_context():
        hunt = db.session.get(Hunt, hunt_id)
        if hunt and hunt.status == "active":
            _end_hunt(hunt)


# --------------------------------------------------------------------------- #
# Hunt session management                                                     #
# --------------------------------------------------------------------------- #
@app.route("/api/hunt/create", methods=["POST"])
def create_hunt():
    data = request.get_json(silent=True) or {}
    try:
        duration = int(data.get("duration", 30))
    except (ValueError, TypeError):
        duration = 30
    if duration not in VALID_DURATIONS:
        duration = 30
    host_name = (data.get("host_name") or "Host").strip()[:40] or "Host"

    code = _generate_code()
    hunt = Hunt(id=code, host_name=host_name, duration=duration, status="waiting")
    db.session.add(hunt)

    # The host plays too — give them a Player row so they appear on the leaderboard.
    sid = _ensure_session_id()
    host_player = Player(hunt_id=code, name=host_name, session_id=sid, score=0)
    db.session.add(host_player)
    db.session.commit()

    session["player_id"] = host_player.id
    session["hunt_id"] = code
    return jsonify(
        {
            "hunt_id": code,
            "code": code,
            "duration": duration,
            "player_id": host_player.id,
            "player_name": host_name,
            "is_host": True,
            "player_count": 1,
        }
    )


@app.route("/api/hunt/join", methods=["POST"])
def join_hunt():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip().upper()
    player_name = (data.get("player_name") or "Player").strip()[:40] or "Player"

    hunt = db.session.get(Hunt, code)
    if not hunt:
        return jsonify({"success": False, "error": "That code doesn't match a hunt."}), 404
    if hunt.status != "waiting":
        msg = "That hunt has already ended." if hunt.status == "ended" else "That hunt has already started."
        return jsonify({"success": False, "error": msg}), 409

    sid = _ensure_session_id()
    player = Player(hunt_id=code, name=player_name, session_id=sid, score=0)
    db.session.add(player)
    db.session.commit()

    session["player_id"] = player.id
    session["hunt_id"] = code

    player_count = Player.query.filter_by(hunt_id=code).count()
    socketio.emit("player_joined", {"player_name": player_name, "player_count": player_count}, room=code)
    return jsonify(
        {
            "success": True,
            "hunt_id": code,
            "player_id": player.id,
            "player_name": player_name,
            "duration": hunt.duration,
            "player_count": player_count,
        }
    )


@app.route("/api/hunt/start", methods=["POST"])
def start_hunt():
    data = request.get_json(silent=True) or {}
    hunt_id = (data.get("hunt_id") or "").strip().upper()

    hunt = db.session.get(Hunt, hunt_id)
    if not hunt:
        return jsonify({"success": False, "error": "Hunt not found."}), 404
    if hunt.status == "active":
        return jsonify({"success": True, "end_time": (hunt.end_time.isoformat() + "Z")})
    if hunt.status == "ended":
        return jsonify({"success": False, "error": "Hunt already ended."}), 409

    hunt.status = "active"
    hunt.started_at = datetime.utcnow()
    db.session.commit()

    end_time = hunt.end_time.isoformat() + "Z"
    socketio.emit("hunt_started", {"end_time": end_time, "duration": hunt.duration}, room=hunt_id)
    socketio.start_background_task(_schedule_auto_end, hunt_id, hunt.duration)
    return jsonify({"success": True, "end_time": end_time})


@app.route("/api/hunt/<hunt_id>/status")
def hunt_status(hunt_id):
    hunt = db.session.get(Hunt, hunt_id.upper())
    if not hunt:
        return jsonify({"error": "Hunt not found."}), 404
    _maybe_end_hunt(hunt)

    board = _leaderboard(hunt.id)
    me = _current_player(hunt.id)
    your_score, your_rank, your_finds = (me.score if me else 0), None, 0
    if me:
        for row in board:
            if row["player_id"] == me.id:
                your_rank, your_finds = row["rank"], row["finds"]
                break

    return jsonify(
        {
            "status": hunt.status,
            "time_remaining_seconds": _time_remaining(hunt),
            "player_count": len(board),
            "your_score": your_score,
            "your_rank": your_rank,
            "your_finds_count": your_finds,
            "end_time": (hunt.end_time.isoformat() + "Z") if hunt.end_time else None,
            "leaderboard": [{"name": r["name"], "score": r["score"], "finds": r["finds"]} for r in board],
        }
    )


@app.route("/api/hunt/<hunt_id>/leaderboard")
def hunt_leaderboard(hunt_id):
    hunt = db.session.get(Hunt, hunt_id.upper())
    if not hunt:
        return jsonify({"error": "Hunt not found."}), 404
    _maybe_end_hunt(hunt)
    return jsonify({"leaderboard": _leaderboard(hunt.id), "notable_finds": _notable_finds(hunt.id)})


@app.route("/api/hunt/<hunt_id>/my_finds")
def my_finds(hunt_id):
    """This player's finds — lets the frontend rebuild its list after a reload."""
    hunt = db.session.get(Hunt, hunt_id.upper())
    if not hunt:
        return jsonify({"error": "Hunt not found."}), 404
    player = _current_player(hunt.id)
    if not player:
        return jsonify({"finds": [], "score": 0})

    finds = (
        Find.query.filter_by(hunt_id=hunt.id, player_id=player.id)
        .order_by(Find.found_at.desc())
        .all()
    )
    out = []
    for f in finds:
        info = get_plant_info(f.scientific, f.plant_name)
        out.append(
            {
                "key": info["key"],
                "plant_name": f.plant_name,
                "scientific_name": f.scientific,
                "emoji": info["emoji"],
                "points": f.points,
                "is_first": f.is_first,
                "found_at": (f.found_at.isoformat() + "Z") if f.found_at else None,
            }
        )
    return jsonify({"finds": out, "score": player.score or 0})


# --------------------------------------------------------------------------- #
# Plant identification                                                        #
# --------------------------------------------------------------------------- #
@app.route("/api/identify", methods=["POST"])
def identify():
    data = request.get_json(silent=True) or {}
    hunt_id = (data.get("hunt_id") or "").strip().upper()
    image_b64 = data.get("image") or ""

    hunt = db.session.get(Hunt, hunt_id)
    if not hunt:
        return jsonify({"success": False, "message": "Hunt not found."}), 404
    _maybe_end_hunt(hunt)
    if hunt.status != "active":
        return jsonify({"success": False, "message": "This hunt isn't active right now."}), 409

    player = _current_player(hunt_id)
    if not player:
        return jsonify({"success": False, "message": "Join the hunt before scanning plants."}), 403

    if not image_b64:
        return jsonify({"success": False, "message": "No photo received — try again."}), 400

    # Accept a raw base64 string or a full data URL.
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[-1]
    try:
        base64.b64decode(image_b64, validate=True)
    except (binascii.Error, ValueError):
        return jsonify({"success": False, "message": "That photo didn't come through — try again."}), 400

    if not PLANTID_API_KEY:
        return jsonify({"success": False, "message": "Plant identification isn't configured yet."}), 503

    # --- Call Plant.id v3 ---
    try:
        resp = requests.post(
            PLANTID_API_URL,
            params={"details": "common_names"},
            headers={"Api-Key": PLANTID_API_KEY, "Content-Type": "application/json"},
            json={"images": [image_b64], "classification_level": "species"},
            timeout=30,
        )
    except requests.RequestException:
        return jsonify(
            {"success": False, "message": "Couldn't reach the plant identifier — check your connection and try again."}
        ), 502

    if resp.status_code not in (200, 201):
        return jsonify(
            {"success": False, "message": "The plant identifier had a problem — try again in a moment."}
        ), 502

    result = (resp.json() or {}).get("result", {})

    if result.get("is_plant", {}).get("binary") is False:
        return jsonify(
            {"success": False, "message": "Hmm, that doesn't look like a plant — point the camera at a leaf or flower!"}
        )

    suggestions = result.get("classification", {}).get("suggestions", [])
    if not suggestions:
        return jsonify({"success": False, "message": "Couldn't identify that one — try again with better lighting."})

    top = suggestions[0]
    confidence = float(top.get("probability") or 0)
    scientific = (top.get("name") or "").strip()
    common_names = (top.get("details") or {}).get("common_names") or []
    common = common_names[0] if common_names else None

    # (2) Confidence gate
    if confidence < CONFIDENCE_THRESHOLD:
        return jsonify(
            {
                "success": False,
                "message": "Not confident enough — try again with better lighting, get closer, and "
                "make sure the plant fills the frame",
            }
        )

    # (3) Already found by this player?
    if Find.query.filter_by(hunt_id=hunt_id, player_id=player.id, scientific=scientific).first():
        return jsonify({"success": False, "message": "You already found this one!"})

    # (4) Scoring — all plants equal (10), unless promoted in the bonus list; 2x for first finder.
    info = get_plant_info(scientific, common)
    is_first = Find.query.filter_by(hunt_id=hunt_id, scientific=scientific).first() is None
    base_points = info["base_points"]
    points = base_points * 2 if is_first else base_points
    plant_name = info["plant_name"] or common or scientific

    # (5)(6) Save the find and bump the player's score.
    find = Find(
        hunt_id=hunt_id,
        player_id=player.id,
        plant_name=plant_name,
        scientific=scientific,
        rarity=None,
        points=points,
        is_first=is_first,
    )
    db.session.add(find)
    player.score = (player.score or 0) + points
    db.session.commit()

    # (7) Push updates to everyone in the hunt.
    socketio.emit("score_update", {"leaderboard": _leaderboard(hunt_id)}, room=hunt_id)
    if is_first:
        socketio.emit(
            "notable_find",
            {
                "plant_name": plant_name,
                "scientific_name": scientific,
                "finder_name": player.name,
                "emoji": info["emoji"],
                "points": points,
                "is_first": True,
            },
            room=hunt_id,
        )

    # (8) Respond to the scanning player.
    return jsonify(
        {
            "success": True,
            "plant_name": plant_name,
            "scientific_name": scientific,
            "rarity": None,
            "points": points,
            "base_points": base_points,
            "is_first": is_first,
            "confidence": round(confidence, 4),
            "emoji": info["emoji"],
            "key": info["key"],
            "about": info["about"],
            "forage_note": info["forage_note"],
            "climate_impact": info["climate_impact"],
        }
    )


# --------------------------------------------------------------------------- #
# SocketIO                                                                     #
# --------------------------------------------------------------------------- #
@socketio.on("join_room")
def on_join_room(data):
    hunt_id = (data or {}).get("hunt_id")
    if hunt_id:
        join_room(hunt_id.strip().upper())


# --------------------------------------------------------------------------- #
# Frontend + health                                                           #
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # allow_unsafe_werkzeug lets the bundled server run outside debug mode for local
    # use; in production the Procfile launches gunicorn instead of this entrypoint.
    socketio.run(app, host="0.0.0.0", port=port, debug=DEBUG, allow_unsafe_werkzeug=True)
