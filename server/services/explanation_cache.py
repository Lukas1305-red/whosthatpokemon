"""Thread-safe, process-local caching for generated Pokémon explanations."""

import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class _KeyLock:
    lock: Lock = field(default_factory=Lock)
    users: int = 0


class ExplanationCache:
    """A bounded TTL cache that coalesces concurrent requests for the same key.

    This implementation is intentionally process-local. It is suitable for the
    single-process deployment used by this app; replace it with a shared Redis
    implementation before running multiple API workers or replicas.
    """

    def __init__(
        self,
        ttl_seconds: int,
        max_entries: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than 0")
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")

        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.clock = clock
        self._entries: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._entry_lock = Lock()
        self._key_locks: dict[str, _KeyLock] = {}

    def get_or_create(self, key: str, create: Callable[[], str]) -> str:
        cached = self._get(key)
        if cached is not None:
            return cached

        # Prevent a cache stampede: identical concurrent requests wait for the
        # first request's provider call, then use the newly stored answer.
        key_lock = self._acquire_key_lock(key)
        try:
            cached = self._get(key)
            if cached is not None:
                return cached

            value = create()
            self._set(key, value)
            return value
        finally:
            self._release_key_lock(key, key_lock)

    def _get(self, key: str) -> str | None:
        with self._entry_lock:
            entry = self._entries.get(key)
            if entry is None:
                return None

            expires_at, value = entry
            if expires_at <= self.clock():
                del self._entries[key]
                return None

            self._entries.move_to_end(key)
            return value

    def _set(self, key: str, value: str) -> None:
        with self._entry_lock:
            self._entries[key] = (self.clock() + self.ttl_seconds, value)
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def _acquire_key_lock(self, key: str) -> _KeyLock:
        with self._entry_lock:
            key_lock = self._key_locks.setdefault(key, _KeyLock())
            key_lock.users += 1
        key_lock.lock.acquire()
        return key_lock

    def _release_key_lock(self, key: str, key_lock: _KeyLock) -> None:
        key_lock.lock.release()
        with self._entry_lock:
            key_lock.users -= 1
            if key_lock.users == 0 and self._key_locks.get(key) is key_lock:
                del self._key_locks[key]
