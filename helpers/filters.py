"""
Access control: per-key, per-tier gating.

Tiers (configurable via ACCESS_KEYS env var):
    free        - basic playback, duration-limited
    pro         - longer tracks, priority queue
    enterprise  - no limits, multiple concurrent chats

A chat "unlocks" a tier by running /auth <key> once. The mapping is kept
in memory here; for production persistence swap in Redis/Postgres.
"""

from config import ACCESS_KEYS, DEFAULT_TIER, OWNER_ID, SUDO_USERS

TIER_LIMITS = {
    "free": {"max_duration_min": 10, "concurrent_chats": 1},
    "pro": {"max_duration_min": 60, "concurrent_chats": 5},
    "enterprise": {"max_duration_min": 0, "concurrent_chats": 0},  # 0 = unlimited
}

_authorized_chats: dict[int, str] = {}


def authorize_chat(chat_id: int, key: str) -> bool:
    tier = ACCESS_KEYS.get(key)
    if not tier:
        return False
    _authorized_chats[chat_id] = tier
    return True


def revoke_chat(chat_id: int):
    _authorized_chats.pop(chat_id, None)


def get_tier(chat_id: int) -> str:
    return _authorized_chats.get(chat_id, DEFAULT_TIER)


def tier_limits(chat_id: int) -> dict:
    return TIER_LIMITS.get(get_tier(chat_id), TIER_LIMITS["free"])


def is_owner_or_sudo(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in SUDO_USERS
