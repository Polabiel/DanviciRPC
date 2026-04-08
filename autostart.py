"""Auto-start registration for DaVinciRPC.

Registers (or removes) the application from the OS startup mechanism so it
launches automatically when the user logs in.

Platform support
----------------
- **Windows**: ``HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run``
- **Linux**: ``~/.config/autostart/davincirpc.desktop``  (XDG standard)
- **macOS**: ``~/Library/LaunchAgents/com.davincirpc.app.plist``
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from logger import get_logger

_log = get_logger("autostart")

_APP_NAME = "DaVinciRPC"
_REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# ── Public API ────────────────────────────────────────────────────────────────


def enable() -> bool:
    """Register DaVinciRPC to start automatically on login.

    Returns:
        ``True`` on success, ``False`` if the operation failed or is unsupported.
    """
    exe = _get_executable()
    if exe is None:
        _log.warning("Cannot determine executable path — skipping autostart setup.")
        return False

    if sys.platform == "win32":
        return _win_enable(exe)
    if sys.platform == "darwin":
        return _mac_enable(exe)
    return _linux_enable(exe)


def disable() -> bool:
    """Remove DaVinciRPC from automatic startup.

    Returns:
        ``True`` on success (or if the entry did not exist),
        ``False`` if removal failed.
    """
    if sys.platform == "win32":
        return _win_disable()
    if sys.platform == "darwin":
        return _mac_disable()
    return _linux_disable()


def is_enabled() -> bool:
    """Return ``True`` when the auto-start entry is currently registered."""
    if sys.platform == "win32":
        return _win_is_enabled()
    if sys.platform == "darwin":
        return _mac_is_enabled()
    return _linux_is_enabled()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_executable() -> Optional[str]:
    """Return the path to the running executable.

    When packaged with PyInstaller, ``sys.frozen`` is set and
    ``sys.executable`` points to the bundle.  When running from source,
    we construct a ``python path/to/main.py`` command string instead.
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    # Running from source — build an invocation string
    main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return f'"{sys.executable}" "{main_py}"'


# ── Windows ───────────────────────────────────────────────────────────────────


def _win_enable(exe: str) -> bool:
    try:
        import winreg  # type: ignore[import]

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REGISTRY_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, exe)
        _log.info("Autostart enabled (Windows registry).")
        return True
    except OSError as exc:
        _log.warning("Failed to set autostart registry value: %s", exc)
        return False


def _win_disable() -> bool:
    try:
        import winreg  # type: ignore[import]

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REGISTRY_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            try:
                winreg.DeleteValue(key, _APP_NAME)
            except FileNotFoundError:
                pass  # already absent
        _log.info("Autostart disabled (Windows registry).")
        return True
    except OSError as exc:
        _log.warning("Failed to remove autostart registry value: %s", exc)
        return False


def _win_is_enabled() -> bool:
    try:
        import winreg  # type: ignore[import]

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REGISTRY_KEY,
            0,
            winreg.KEY_READ,
        ) as key:
            try:
                winreg.QueryValueEx(key, _APP_NAME)
                return True
            except FileNotFoundError:
                return False
    except OSError:
        return False


# ── Linux ─────────────────────────────────────────────────────────────────────


def _linux_desktop_path() -> str:
    config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(config_home, "autostart", "davincirpc.desktop")


def _linux_enable(exe: str) -> bool:
    path = _linux_desktop_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={_APP_NAME}\n"
            "Comment=DaVinci Resolve Discord Rich Presence\n"
            f"Exec={exe}\n"
            "Hidden=false\n"
            "NoDisplay=false\n"
            "X-GNOME-Autostart-enabled=true\n"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        _log.info("Autostart enabled (Linux .desktop: %s).", path)
        return True
    except OSError as exc:
        _log.warning("Failed to write autostart .desktop file: %s", exc)
        return False


def _linux_disable() -> bool:
    path = _linux_desktop_path()
    try:
        if os.path.exists(path):
            os.remove(path)
        _log.info("Autostart disabled (Linux .desktop removed).")
        return True
    except OSError as exc:
        _log.warning("Failed to remove autostart .desktop file: %s", exc)
        return False


def _linux_is_enabled() -> bool:
    return os.path.isfile(_linux_desktop_path())


# ── macOS ─────────────────────────────────────────────────────────────────────


def _mac_plist_path() -> str:
    return os.path.expanduser(
        "~/Library/LaunchAgents/com.davincirpc.app.plist"
    )


def _mac_enable(exe: str) -> bool:
    path = _mac_plist_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
            ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n'
            "<dict>\n"
            f"    <key>Label</key><string>com.davincirpc.app</string>\n"
            "    <key>ProgramArguments</key>\n"
            "    <array>\n"
            f"        <string>{exe}</string>\n"
            "    </array>\n"
            "    <key>RunAtLoad</key><true/>\n"
            "    <key>KeepAlive</key><false/>\n"
            "</dict>\n"
            "</plist>\n"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        _log.info("Autostart enabled (macOS LaunchAgent: %s).", path)
        return True
    except OSError as exc:
        _log.warning("Failed to write macOS LaunchAgent plist: %s", exc)
        return False


def _mac_disable() -> bool:
    path = _mac_plist_path()
    try:
        if os.path.exists(path):
            os.remove(path)
        _log.info("Autostart disabled (macOS LaunchAgent removed).")
        return True
    except OSError as exc:
        _log.warning("Failed to remove macOS LaunchAgent plist: %s", exc)
        return False


def _mac_is_enabled() -> bool:
    return os.path.isfile(_mac_plist_path())
