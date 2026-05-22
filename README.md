# 🌿 SproutQuest

A kid-friendly, multiplayer **nature scavenger hunt**. A host starts a timed hunt,
friends join with a code, and everyone races to identify real plants with their
phone camera. The first person to find a species scores **2×**; live leaderboard
and celebrations keep it exciting; when the timer hits zero everyone sees their
final score and the plants they discovered.

Works in a **phone browser — no app install**.

---

## Tech stack

| Piece | Choice |
|---|---|
| Backend | Flask (Python 3.11) |
| Database | SQLite via SQLAlchemy |
| Real-time | Flask-SocketIO (`threading` mode — WebSocket when available, else long-polling) |
| Plant ID | [Plant.id](https://web.plant.id) API **v3** |
| Frontend | Single HTML file (`static/index.html`) served by Flask |
| Deploy | Railway (`Procfile` + gunicorn) |

> **Why threading mode (not eventlet)?** Eventlet is officially deprecated and
> won't start cleanly on modern Python/Windows. Threading mode needs no
> monkey-patching, behaves identically locally and on Railway, and Socket.IO
> still upgrades to WebSocket via `simple-websocket` when the server supports it.

---

## Project layout

```
NatureQuest/
├─ app.py              # Flask app: auth, hunts, identify, SocketIO, timer
├─ models.py           # SQLAlchemy models: Hunt, Player, Find
├─ plant_catalog.py    # Plant data + scoring (incl. the bonus-points knob)
├─ bonus_plants.json   # YOUR master list of plants worth more points
├─ static/index.html   # The game frontend (wired to the backend)
├─ requirements.txt
├─ Procfile            # Railway start command
├─ .env.example        # Template for required secrets
└─ _design_handoff/    # Original design reference (not used at runtime)
```

---

## Local setup

```powershell
# 1. From the project folder, create a virtualenv and install deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. Create your .env from the template and fill it in
copy .env.example .env                  # macOS/Linux: cp .env.example .env

# 3. Run it
python app.py
```

Then open **http://127.0.0.1:5000** on your computer, or your computer's LAN IP
on your phone. The login password is whatever you set as `SPROUTQUEST_PASSWORD`.

> **Camera note:** browsers only allow camera access on a **secure context** —
> `localhost`/`127.0.0.1` or any **https** site. On a phone testing over your LAN
> (`http://192.168.x.x`) the live camera is blocked, so the app automatically
> shows a **"Pick a photo"** upload button instead. On the deployed Railway URL
> (https) the live camera works normally.

### Getting a Plant.id API key

1. Sign up at **https://web.plant.id**.
2. Open the **API** tab and copy your key.
3. Put it in `.env` as `PLANTID_API_KEY=...`.

The free tier includes a limited number of identifications — plenty for testing.

---

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `PLANTID_API_KEY` | ✅ | Your Plant.id v3 API key |
| `SPROUTQUEST_PASSWORD` | ✅ | The single shared password all players type to enter |
| `SECRET_KEY` | ✅ (prod) | Signs session cookies. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `BONUS_PLANTS` | optional | JSON map of plant → points (overrides `bonus_plants.json`); see below |
| `CONFIDENCE_THRESHOLD` | optional | Min species confidence to accept a find (default `0.95`; lower it, e.g. `0.8`, if real kid photos miss too often) |
| `DATABASE_PATH` | optional | SQLite file path (defaults next to `app.py`) |
| `PORT` | optional | Port to bind (Railway sets this automatically) |
| `FLASK_DEBUG` | optional | `1` enables debug mode locally |

---

## Scoring & the master bonus list

Every plant is worth **10 points**, and the **first finder** of a species in a
hunt gets **2× (20 points)**. There are no rarity tiers.

To make **certain plants score higher** (e.g. species that matter in a particular
area), edit **`bonus_plants.json`** — map a plant to a custom point value. The key
can be a scientific name or the friendly catalog key:

```json
{
  "Asclepias syriaca": 50,
  "trillium": 30
}
```

That makes milkweed worth 50 (100 for the first finder) and trillium 30. Keys
starting with `_` are ignored, so the examples shipped in the file are inactive
until you add real entries.

On Railway you can do the same **without redeploying** by setting the
`BONUS_PLANTS` environment variable to the same JSON — handy for changing which
plants score higher per location.

---

## How a hunt works

1. **Login** with the shared password.
2. **Host:** pick a duration (15/30/45/60 min) → **Create Hunt** → share the code → **Begin Hunt**.
3. **Players:** enter the code → wait in the lobby → the hunt starts for everyone when the host hits Begin.
4. **Scan** plants with the camera. ≥95% confidence identifications count; tap a find to read its fun fact, foraging note, and human-impact note.
5. **Leaderboard** updates live; a notification fires when someone is first to find a species.
6. **Time's up** → everyone sees their final score and a recap of every plant they found.

---

## API reference (quick)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/login` | `{password}` → sets session cookie |
| `POST` | `/api/hunt/create` | `{duration, host_name}` → `{code, hunt_id, ...}` |
| `POST` | `/api/hunt/join` | `{code, player_name}` → joins, emits `player_joined` |
| `POST` | `/api/hunt/start` | `{hunt_id}` → starts timer, emits `hunt_started` |
| `GET` | `/api/hunt/<id>/status` | live status + leaderboard |
| `GET` | `/api/hunt/<id>/leaderboard` | full leaderboard + notable (first) finds |
| `GET` | `/api/hunt/<id>/my_finds` | the current player's finds |
| `POST` | `/api/identify` | `{image, hunt_id}` → identifies & scores a plant |
| `GET` | `/ping` | health check → `{"status":"ok"}` |

**SocketIO events** (room = hunt code): client emits `join_room`; server emits
`player_joined`, `hunt_started`, `score_update`, `notable_find`, `hunt_ended`.

---

## Deploying to Railway

1. Push this folder to a Git repo and create a new Railway project from it.
2. In **Variables**, set `PLANTID_API_KEY`, `SPROUTQUEST_PASSWORD`, and `SECRET_KEY`
   (and optionally `BONUS_PLANTS`).
3. Railway uses the `Procfile`:
   ```
   web: gunicorn --worker-class gthread --workers 1 --threads 8 --bind 0.0.0.0:$PORT app:app
   ```
4. Deploy. Open the generated **https** URL on your phone — the live camera works there.

> **Notes / limitations**
> - SQLite lives on the container's local disk, so hunt history **resets on
>   redeploy**. That's fine for live games; attach a persistent volume or move to
>   Postgres if you need durable history.
> - Run a **single worker** (as the Procfile does). Scaling to multiple workers
>   needs a shared message queue — add `message_queue="redis://..."` to the
>   `SocketIO(...)` call in `app.py` and a Redis service.
