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
        for proc in psutil.process_iter(["name"]):
            name = (proc.info.get("name") or "").lower()
            if name == target:
                return True
    except psutil.AccessDenied as exc:
        _log.warning("Access denied while iterating processes: %s", exc)
    except psutil.NoSuchProcess:
        pass  # process vanished between iteration and attribute access
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
    except (AttributeError, RuntimeError, OSError) as exc:
        _log.warning("Failed to enumerate windows: %s", exc)
        return FALLBACK_MODE

    resolve_titles = [t for t in windows if "davinci resolve" in t.lower() or "resolve" in t.lower()]

    if not resolve_titles:
        return FALLBACK_MODE

    title_lower = resolve_titles[0].lower()
    for keyword, mode in WINDOW_MODE_MAP.items():
        if keyword in title_lower:
            _log.debug("Detected mode %r from window title %r", mode, resolve_titles[0])
            return mode

    return FALLBACK_MODE
