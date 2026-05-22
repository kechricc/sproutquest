"""SQLAlchemy models for SproutQuest.

Three tables back the game:
  - Hunt    : one game session (identified by its shareable join code)
  - Player  : someone who joined a hunt (the host is a player too)
  - Find    : a single confirmed plant identification within a hunt
"""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Hunt(db.Model):
    __tablename__ = "hunts"

    # 6-char uppercase join code, e.g. "OAK247". Doubles as the SocketIO room name.
    id = db.Column(db.String, primary_key=True)
    host_name = db.Column(db.String, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    started_at = db.Column(db.DateTime, nullable=True)  # null until host starts
    ended_at = db.Column(db.DateTime, nullable=True)    # null until timer expires
    status = db.Column(db.String, nullable=False, default="waiting")  # waiting | active | ended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    players = db.relationship("Player", backref="hunt", lazy=True, cascade="all, delete-orphan")
    finds = db.relationship("Find", backref="hunt", lazy=True, cascade="all, delete-orphan")

    @property
    def end_time(self):
        """When the hunt ends, as a datetime, or None if not started."""
        if not self.started_at:
            return None
        from datetime import timedelta
        return self.started_at + timedelta(minutes=self.duration)


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hunt_id = db.Column(db.String, db.ForeignKey("hunts.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    session_id = db.Column(db.String, nullable=False)  # browser session that owns this player
    score = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    finds = db.relationship("Find", backref="player", lazy=True, cascade="all, delete-orphan")


class Find(db.Model):
    __tablename__ = "finds"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hunt_id = db.Column(db.String, db.ForeignKey("hunts.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    plant_name = db.Column(db.String)        # common name shown to players
    scientific = db.Column(db.String)        # scientific name (species-level identity key)
    rarity = db.Column(db.String)            # reserved; unused for now (no rarities)
    points = db.Column(db.Integer)
    is_first = db.Column(db.Boolean, default=False)  # first to find this species in this hunt
    found_at = db.Column(db.DateTime, default=datetime.utcnow)
