"""In-memory conversation store; data is cleared when the process stops."""
from __future__ import annotations

from collections import defaultdict, deque
from threading import RLock
from typing import Deque


class MemoryStore:
    def __init__(self, max_items: int = 12) -> None:
        self._max_items = max(2, max_items)
        self._items: dict[int, Deque[tuple[str, str]]] = defaultdict(
            lambda: deque(maxlen=self._max_items)
        )
        self._lock = RLock()

    def add(self, user_id: int, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")
        with self._lock:
            self._items[user_id].append((role, content))

    def get(self, user_id: int) -> list[tuple[str, str]]:
        with self._lock:
            return list(self._items.get(user_id, ()))

    def clear(self, user_id: int) -> None:
        with self._lock:
            self._items.pop(user_id, None)
