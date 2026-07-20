"""
UNICEIF Music Bot — Configuration
All values are loaded from environment variables so nothing sensitive
is ever hard-coded in the repo. Set these in Render's Environment tab.
"""

import os


def _int(name: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _list(name: str):
    raw = os.environ.get(name, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


# ---- Telegram API credentials (my.telegram.org) ----
API_ID = _int("API_ID")
API_HASH = os.environ.get("API_HASH", "")

# ---- Bot account (BotFather) ----
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ---- Assistant / userbot session string ----
# The assistant account is what actually joins the voice chat.
# Generate it once locally with helpers/generate_session.py
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# ---- Ownership & access control ----
OWNER_ID = _int("OWNER_ID")
SUDO_USERS = set(_int(x) if x.isdigit() else 0 for x in _list("SUDO_USERS"))

# ---- Per-key / per-tier access (Free -> Enterprise) ----
# ACCESS_KEYS is a comma separated list of "key:tier" pairs, e.g.
# ACCESS_KEYS=free-123:free,pro-999:enterprise
ACCESS_KEYS_RAW = _list("ACCESS_KEYS")
ACCESS_KEYS = {}
for pair in ACCESS_KEYS_RAW:
    if ":" in pair:
        k, tier = pair.split(":", 1)
        ACCESS_KEYS[k.strip()] = tier.strip().lower()

# ---- Logging ----
LOG_GROUP_ID = _int("LOG_GROUP_ID")

# ---- Playback tuning ----
DURATION_LIMIT_MIN = _int("DURATION_LIMIT_MIN", 120)  # max track length allowed
AUTO_LEAVE_SECONDS = _int("AUTO_LEAVE_SECONDS", 300)  # idle auto-leave
DEFAULT_TIER = os.environ.get("DEFAULT_TIER", "free")

# ---- ffmpeg / streaming quality ----
AUDIO_BITRATE = os.environ.get("AUDIO_BITRATE", "48k")
STREAM_QUALITY = os.environ.get("STREAM_QUALITY", "high")  # low/medium/high

PING_TEXT = "🎧 UNICEIF Music Bot is alive."
