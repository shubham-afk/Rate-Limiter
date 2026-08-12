"""The intentionally simple, single-process fixed-window limiter for Phase 1."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import time
from typing import Callable


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    remaining: int
    reset_at: float


@dataclass
class _WindowState:
    window_number: int
    count: int


class FixedWindowLimiter:
    """A lock-protected counter map, scoped to this one Python process.

    The fixed window is derived from ``floor(now / window_seconds)``. This is
    purposefully not a sliding window: callers can use a full quota immediately
    before a boundary and another full quota immediately after it.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        clock: Callable[[], float] = time,
    ) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._states: dict[str, _WindowState] = {}
        self._lock = Lock()

    def check(self, identity: str) -> LimitDecision:
        now = self._clock()
        window_number = int(now // self.window_seconds)
        reset_at = (window_number + 1) * self.window_seconds

        # Checking and incrementing must occur under one lock. This prevents a
        # same-process check-then-increment race; it does not make the map safe
        # across multiple Django instances (the Phase 2 problem).
        with self._lock:
            state = self._states.get(identity)
            if state is None or state.window_number != window_number:
                state = _WindowState(window_number=window_number, count=0)
                self._states[identity] = state

            if state.count >= self.limit:
                return LimitDecision(False, 0, reset_at)

            state.count += 1
            return LimitDecision(True, self.limit - state.count, reset_at)

    def clear(self) -> None:
        """Clear all in-memory counters; useful for a local development reset."""
        with self._lock:
            self._states.clear()
