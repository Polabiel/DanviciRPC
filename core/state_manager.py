"""Application state — single source of truth for the RPC loop."""

from dataclasses import dataclass, field
from typing import Optional

from config import FALLBACK_MODE, FALLBACK_PROJECT
from logger import get_logger

_log = get_logger("core.state_manager")


@dataclass
class AppState:
    """Immutable snapshot of the current application state."""

    resolve_active: bool = False
    mode: str = FALLBACK_MODE
    project_name: str = FALLBACK_PROJECT
    timeline_name: Optional[str] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AppState):
            return NotImplemented
        return (
            self.resolve_active == other.resolve_active
            and self.mode == other.mode
            and self.project_name == other.project_name
            and self.timeline_name == other.timeline_name
        )


class StateManager:
    """Owns and compares application state to avoid redundant RPC updates.

    Usage
    -----
    .. code-block:: python

        sm = StateManager()
        new_state = AppState(resolve_active=True, mode="Edit", project_name="MyFilm")
        if sm.update(new_state):
            # state changed — push to Discord
            ...
    """

    def __init__(self) -> None:
        self._current: AppState = AppState()

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def current(self) -> AppState:
        """The last recorded state."""
        return self._current

    def update(self, new_state: AppState) -> bool:
        """Compare *new_state* with the cached state.

        Returns:
            ``True`` when the state has changed and an RPC update is needed.
            ``False`` when the state is identical (no update required).
        """
        changed = new_state != self._current
        if changed:
            _log.info(
                "State changed: resolve_active=%s mode=%r project=%r",
                new_state.resolve_active,
                new_state.mode,
                new_state.project_name,
            )
            self._current = new_state
        return changed
