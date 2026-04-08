"""Session time tracker — maintains continuous elapsed time across updates."""

import time
from typing import Optional

from logger import get_logger

_log = get_logger("core.session")


class SessionTracker:
    """Tracks a single editing session's start time.

    The tracker keeps a *monotonic* baseline so it is never affected by
    system clock changes.  The ``start_timestamp`` exposed to Discord is a
    regular Unix timestamp computed once when the session begins.

    Lifecycle
    ---------
    * ``start()``  — called when DaVinci Resolve becomes active.
    * ``pause()``  — called when Resolve exits; accumulates elapsed time.
    * ``resume()`` — called when Resolve re-opens; restarts monotonic clock.
    * ``reset()``  — full reset (new session).
    """

    def __init__(self) -> None:
        self._session_start_unix: Optional[float] = None   # for Discord ``start``
        self._mono_start: Optional[float] = None           # monotonic reference
        self._accumulated: float = 0.0                     # seconds accumulated while paused
        self._active: bool = False

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        """``True`` when the session is currently running."""
        return self._active

    @property
    def start_timestamp(self) -> Optional[float]:
        """Unix timestamp of the *effective* session start (for Discord RPC).

        Adjusts for any previously accumulated time so Discord displays the
        correct total elapsed duration.
        """
        if self._session_start_unix is None:
            return None
        # Shift the displayed start backwards by the already-accumulated time
        return self._session_start_unix - self._accumulated

    @property
    def elapsed_seconds(self) -> float:
        """Total elapsed seconds including any previously paused intervals."""
        if not self._active or self._mono_start is None:
            return self._accumulated
        return self._accumulated + (time.monotonic() - self._mono_start)

    def start(self) -> None:
        """Begin a brand-new session (clears any previous state)."""
        self.reset()
        self._begin()
        _log.info("Session started.")

    def pause(self) -> None:
        """Pause the running session without losing elapsed time."""
        if not self._active:
            return
        if self._mono_start is not None:
            self._accumulated += time.monotonic() - self._mono_start
        self._mono_start = None
        self._active = False
        _log.info("Session paused — accumulated %.1fs.", self._accumulated)

    def resume(self) -> None:
        """Resume a previously paused session."""
        if self._active:
            return
        self._session_start_unix = time.time()
        self._mono_start = time.monotonic()
        self._active = True
        _log.info("Session resumed — accumulated %.1fs so far.", self._accumulated)

    def reset(self) -> None:
        """Completely reset all state."""
        self._session_start_unix = None
        self._mono_start = None
        self._accumulated = 0.0
        self._active = False

    # ── Private helpers ───────────────────────────────────────────────────────

    def _begin(self) -> None:
        self._session_start_unix = time.time()
        self._mono_start = time.monotonic()
        self._active = True
