"""
Simple in-memory per-chat queue manager.
For multi-instance / enterprise scaling, swap the dict for Redis —
the interface below is intentionally minimal so that's a drop-in change.
"""

from collections import deque


class QueueManager:
    def __init__(self):
        self._queues: dict[int, deque] = {}
        self._now_playing: dict[int, dict] = {}

    def add(self, chat_id: int, track: dict):
        self._queues.setdefault(chat_id, deque()).append(track)

    def pop_next(self, chat_id: int):
        q = self._queues.get(chat_id)
        if q and len(q):
            return q.popleft()
        return None

    def peek_all(self, chat_id: int):
        return list(self._queues.get(chat_id, []))

    def set_playing(self, chat_id: int, track: dict | None):
        if track is None:
            self._now_playing.pop(chat_id, None)
        else:
            self._now_playing[chat_id] = track

    def now_playing(self, chat_id: int):
        return self._now_playing.get(chat_id)

    def clear(self, chat_id: int):
        self._queues.pop(chat_id, None)
        self._now_playing.pop(chat_id, None)

    def has_pending(self, chat_id: int) -> bool:
        return bool(self._queues.get(chat_id))


queue_manager = QueueManager()
