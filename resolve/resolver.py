"""Thin wrapper around the DaVinciResolveScript API.

The Resolve scripting API is only available when DaVinci Resolve is running
and the correct Python environment is set up.  All calls are guarded so the
rest of the application continues working in "heuristic mode" when the API is
not accessible.
"""

import importlib
import sys
from typing import Optional

from config import ENABLE_RESOLVE_API, FALLBACK_PROJECT
from logger import get_logger

_log = get_logger("resolve.resolver")


def _load_resolve_module() -> Optional[object]:
    """Attempt to import ``DaVinciResolveScript``.

    Returns the module object or ``None`` if it cannot be loaded.
    """
    try:
        module = importlib.import_module("DaVinciResolveScript")
        return module
    except ModuleNotFoundError:
        # Try the alternative path set by Resolve on some installations
        _try_add_resolve_path()
        try:
            module = importlib.import_module("DaVinciResolveScript")
            return module
        except ModuleNotFoundError:
            return None


def _try_add_resolve_path() -> None:
    """Add Resolve's script path to sys.path when running on Windows/macOS."""
    import os

    candidates = [
        # macOS
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
        # Windows
        r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
        # Linux
        "/opt/resolve/libs/Fusion/",
    ]
    for path in candidates:
        if os.path.isdir(path) and path not in sys.path:
            sys.path.append(path)
            _log.debug("Added Resolve scripting path: %s", path)


class ResolveClient:
    """Communicates with the running DaVinci Resolve instance via its API.

    Attributes
    ----------
    available:
        ``True`` when the API was successfully contacted during initialisation.
    """

    def __init__(self) -> None:
        self._resolve: Optional[object] = None
        self.available: bool = False

        if not ENABLE_RESOLVE_API:
            _log.info("ENABLE_RESOLVE_API is False — Resolve API disabled.")
            return

        self._connect()

    # ── Public interface ──────────────────────────────────────────────────────

    def get_project_name(self) -> str:
        """Return the active project's name, or a fallback string."""
        project = self._get_current_project()
        if project is None:
            return FALLBACK_PROJECT
        try:
            name: str = project.GetName()
            return name if name else FALLBACK_PROJECT
        except AttributeError as exc:
            _log.warning("Could not read project name: %s", exc)
            return FALLBACK_PROJECT

    def get_timeline_name(self) -> Optional[str]:
        """Return the active timeline's name, or ``None`` if unavailable."""
        project = self._get_current_project()
        if project is None:
            return None
        try:
            timeline = project.GetCurrentTimeline()
            if timeline is None:
                return None
            name: str = timeline.GetName()
            return name if name else None
        except AttributeError as exc:
            _log.warning("Could not read timeline name: %s", exc)
            return None

    def refresh(self) -> None:
        """Re-attempt a connection if the client is not yet available."""
        if not self.available:
            self._connect()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _connect(self) -> None:
        module = _load_resolve_module()
        if module is None:
            _log.warning(
                "DaVinciResolveScript module not found — running in heuristic mode."
            )
            return

        try:
            resolve_obj = module.scriptapp("Resolve")  # type: ignore[attr-defined]
            if resolve_obj is None:
                _log.warning("Resolve API returned None — is Resolve running?")
                return
            self._resolve = resolve_obj
            self.available = True
            _log.info("Connected to DaVinci Resolve API successfully.")
        except (AttributeError, RuntimeError, OSError) as exc:
            _log.warning("Failed to connect to Resolve API: %s", exc)

    def _get_current_project(self) -> Optional[object]:
        """Return the current project object, refreshing the connection if needed."""
        if not self.available or self._resolve is None:
            return None
        try:
            pm = self._resolve.GetProjectManager()  # type: ignore[attr-defined]
            if pm is None:
                return None
            return pm.GetCurrentProject()
        except (AttributeError, RuntimeError, OSError) as exc:
            _log.warning("Lost connection to Resolve API: %s", exc)
            self.available = False
            self._resolve = None
            return None
