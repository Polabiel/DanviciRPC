"""Detect whether DaVinci Resolve is running and which editing page is active."""

import platform
import sys
from typing import Optional

import psutil

from config import (
    FALLBACK_MODE,
    RESOLVE_PROCESS_LINUX,
    RESOLVE_PROCESS_WINDOWS,
    WINDOW_MODE_MAP,
)
from logger import get_logger

_log = get_logger("resolve.detector")

_PLATFORM = sys.platform


def _get_process_name() -> str:
    """Return the expected Resolve process name for the current platform."""
    if _PLATFORM == "win32":
        return RESOLVE_PROCESS_WINDOWS
    return RESOLVE_PROCESS_LINUX


def is_resolve_running() -> bool:
    """Check whether a DaVinci Resolve process is currently active.

    Returns:
        ``True`` if Resolve is running, ``False`` otherwise.
    """
    target = _get_process_name().lower()
    try:
        for proc in psutil.process_iter(["name", "pid"]):
            name = (proc.info.get("name") or "").lower()
            pid = proc.info.get("pid")
            if name == target:
                _log.info("Resolve process detected: %s (pid=%s)", proc.info.get("name"), pid)
                return True
    except psutil.AccessDenied as exc:
        _log.warning("Access denied while iterating processes: %s", exc)
    except psutil.NoSuchProcess:
        pass  # process vanished between iteration and attribute access
    _log.debug("No Resolve process detected")
    return False


def detect_mode_from_window() -> str:
    """Infer the active editing page from the Resolve window title.

    Attempts to import ``pygetwindow`` at runtime so the rest of the
    application still works when the library is unavailable (e.g. on Linux
    headless environments).

    Returns:
        A human-readable mode string (e.g. ``"Color Grading"``, ``"Edit"``)
        or :data:`config.FALLBACK_MODE` when detection is impossible.
    """
    try:
        import pygetwindow as gw  # type: ignore[import-untyped]
    except (ImportError, NotImplementedError):
        _log.warning(
            "pygetwindow is not available on this platform — "
            "window-title detection disabled."
        )
        return FALLBACK_MODE

    try:
        windows = gw.getAllTitles()
        _log.debug("Enumerated %d window titles for mode detection.", len(windows) if windows is not None else 0)
    except (AttributeError, RuntimeError, OSError) as exc:
        _log.warning("Failed to enumerate windows: %s", exc)
        return FALLBACK_MODE

    resolve_titles = [t for t in windows if t and ("davinci resolve" in t.lower() or "resolve" in t.lower())]
    _log.debug("Resolve window titles found: %d", len(resolve_titles))

    if not resolve_titles:
        _log.debug("No Resolve window titles matched — using fallback mode %r", FALLBACK_MODE)
        return FALLBACK_MODE

    title_lower = resolve_titles[0].lower()
    for keyword, mode in WINDOW_MODE_MAP.items():
        if keyword in title_lower:
            _log.debug("Detected mode %r from window title", mode)
            return mode

    _log.debug("No keyword matched in Resolve title — using fallback mode %r", FALLBACK_MODE)
    return FALLBACK_MODE


def detect_project_from_window() -> Optional[str]:
    """Try to extract the project name from the Resolve window title.

    Handles common title formats such as:
      - "DaVinci Resolve - <Project Name>"
      - "<Project Name> - DaVinci Resolve"

    Returns the project name string or ``None`` when it cannot be determined.
    """
    try:
        import pygetwindow as gw  # type: ignore[import-untyped]
    except (ImportError, NotImplementedError):
        _log.debug("pygetwindow not available — cannot detect project from window title")
        return None

    try:
        windows = gw.getAllTitles()
    except (AttributeError, RuntimeError, OSError) as exc:
        _log.debug("Failed to enumerate windows for project detection: %s", exc)
        return None

    resolve_titles = [t for t in windows if t and ("davinci resolve" in t.lower() or "resolve" in t.lower())]
    if not resolve_titles:
        return None

    for title in resolve_titles:
        t = title.strip()
        lower = t.lower()

        # Pattern: "DaVinci Resolve - Project Name"
        marker = "davinci resolve - "
        if marker in lower:
            idx = lower.find(marker)
            project = t[idx + len(marker) :].strip()
            if project:
                _log.debug("Detected project name from window (pattern 'DaVinci Resolve -')")
                return project

        # Pattern: "Project Name - DaVinci Resolve"
        marker2 = " - davinci resolve"
        if marker2 in lower:
            idx = lower.find(marker2)
            project = t[:idx].strip()
            if project:
                _log.debug("Detected project name from window (pattern '- DaVinci Resolve')")
                return project

    return None
