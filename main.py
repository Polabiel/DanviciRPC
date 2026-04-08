"""DaVinciRPC — main orchestration loop.

Brings together:
- DaVinci Resolve process / window detection
- DaVinci Resolve scripting API (optional)
- Discord Rich Presence updates
- Session timing
- Application state management
- System tray icon (cross-platform)
- Auto-start on login (optional)
"""

import signal
import sys
import time
import os
import psutil
import logging

import autostart as _autostart
from config import UPDATE_INTERVAL, FALLBACK_PROJECT, AUTOSTART_ENABLED, validate as validate_config
from core.session import SessionTracker
from core.state_manager import AppState, StateManager
from discord.rpc_client import RPCClient
from logger import get_logger
from resolve.detector import (
    detect_mode_from_window,
    detect_project_from_window,
    is_resolve_running,
)
from resolve.resolver import ResolveClient

_log = get_logger("main")


def find_conflicting_instances(project_root: str) -> list:
    """Return a list of running processes that look like another instance of this app.

    Heuristics used:
    - Process cmdline contains the absolute path to this project's root
    - Process cmdline contains 'main.py'
    - Process name or exe contains 'resolve-rpc' (packaged binary name)

    Excludes the current process and its parent (the PyInstaller bootstrap
    process when running as a packaged executable).
    """
    current_pid = os.getpid()
    parent_pid = os.getppid()
    matches = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "exe"]):
        try:
            info = proc.info
            pid = info.get("pid")
            if pid == current_pid or pid == parent_pid:
                continue
            name = (info.get("name") or "").lower()
            exe = (info.get("exe") or "")
            cmdline_list = info.get("cmdline") or []
            if isinstance(cmdline_list, (list, tuple)):
                cmdline = " ".join(cmdline_list).lower()
            else:
                cmdline = str(cmdline_list).lower()

            # Require both the project root path AND "main.py" to be in the
            # command line, or a packaged binary name, to avoid false positives.
            if (
                (project_root.lower() in cmdline and "main.py" in cmdline)
                or "resolve-rpc" in name
                or "resolve-rpc" in str(exe).lower()
            ):
                matches.append({"pid": pid, "name": name, "cmdline": cmdline or exe})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return matches

# ── Graceful shutdown ─────────────────────────────────────────────────────────

_shutdown_requested: bool = False


def _handle_signal(signum: int, frame: object) -> None:  # noqa: ARG001
    global _shutdown_requested
    _log.info("Shutdown signal received (%d) — stopping …", signum)
    _shutdown_requested = True


# ── Helpers ────────────────────────────────────────────────────────────────────


def _build_state(
    resolve_client: ResolveClient,
    resolve_active: bool,
) -> AppState:
    """Gather current information and build an :class:`AppState` snapshot.

    Args:
        resolve_client: Live (or stub) Resolve API wrapper.
        resolve_active: Whether a Resolve process was detected.

    Returns:
        A fully-populated :class:`AppState`.
    """
    if not resolve_active:
        return AppState(resolve_active=False)

    mode = detect_mode_from_window()

    # Refresh the API connection on each cycle when it has gone away
    resolve_client.refresh()

    if resolve_client.available:
        project_name = resolve_client.get_project_name()
        timeline_name = resolve_client.get_timeline_name()
    else:
        # Fallback: try to parse the project name from the Resolve window title
        project_from_win = detect_project_from_window()
        if project_from_win:
            project_name = project_from_win
            timeline_name = None
            _log.info("Using project name detected from window title: %r", project_name)
        else:
            project_name = FALLBACK_PROJECT
            timeline_name = None

    return AppState(
        resolve_active=True,
        mode=mode,
        project_name=project_name,
        timeline_name=timeline_name,
    )


def _push_rpc(
    rpc: RPCClient,
    state: AppState,
    session: SessionTracker,
) -> None:
    """Send the appropriate presence payload based on *state*.

    Args:
        rpc:     Connected (or auto-reconnecting) RPC client.
        state:   Current application state snapshot.
        session: Session tracker providing the Discord start timestamp.
    """
    if not state.resolve_active:
        _log.info("Preparing to send inactive RPC (Resolve not active)")
        rpc.update_inactive()
        return

    details = f"{state.mode} em andamento"
    project_label = state.project_name
    if state.timeline_name:
        project_label = f"{state.project_name} — {state.timeline_name}"
    rpc_state = f"Projeto: {project_label}"

    _log.info(
        "Preparing to send active RPC update: details=%r state=%r start=%s",
        details,
        rpc_state,
        session.start_timestamp,
    )

    rpc.update_active(
        details=details,
        state=rpc_state,
        start_timestamp=session.start_timestamp,
    )


# ── Main loop ──────────────────────────────────────────────────────────────────


def run(tray_app=None) -> None:
    """Entry point for the main update loop.

    Args:
        tray_app: Optional :class:`tray.TrayApp` instance.  When provided,
                  the tray status label is updated on each state change.
    """
    _log.info("DaVinciRPC starting …")
    validate_config()

    _log.info("Config validation completed.")

    rpc = RPCClient()
    _log.info("RPCClient instantiated.")

    try:
        resolve_client = ResolveClient()
        _log.info("ResolveClient instantiated.")
    except Exception as exc:  # pragma: no cover - defensive
        _log.exception("Exception while creating ResolveClient: %s", exc)
        raise

    session = SessionTracker()
    _log.info("SessionTracker instantiated.")

    state_mgr = StateManager()
    _log.info("StateManager instantiated.")

    # Register OS signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)


    # Optionally enable verbose pypresence logging for debugging
    if os.environ.get("DEBUG_RPC", "false").lower() == "true":
        logging.getLogger("pypresence").setLevel(logging.DEBUG)
        _log.info("Enabled pypresence debug logging")

    # Check for other running instances to avoid conflicts
    project_root = os.path.abspath(os.path.dirname(__file__))
    conflicts = find_conflicting_instances(project_root)
    if conflicts:
        _log.warning("Detected possible conflicting instances running: %s", conflicts)
        if os.environ.get("FORCE_RUN", "false").lower() != "true":
            _log.warning(
                "Another instance appears to be running. Exiting to avoid conflicts. "
                "Set FORCE_RUN=true to override and run anyway."
            )
            return
        _log.info("FORCE_RUN=true — continuing despite detected conflicts")

    # Attempt initial Discord connection (non-fatal if Discord is not open yet)
    rpc.connect()

    _log.info("Entering main loop (interval=%ds) …", UPDATE_INTERVAL)

    try:
        while not _shutdown_requested:
            loop_start = time.monotonic()

            resolve_active = is_resolve_running()

            # ── Session lifecycle management ──────────────────────────────────
            if resolve_active and not session.is_active:
                if session.elapsed_seconds > 0:
                    session.resume()
                else:
                    session.start()

            elif not resolve_active and session.is_active:
                session.pause()

            # ── Build state and decide whether an RPC update is needed ───────
            new_state = _build_state(resolve_client, resolve_active)
            _log.debug("Built state snapshot: %s", new_state)
            state_changed = state_mgr.update(new_state)

            if state_changed or not rpc.connected:
                _push_rpc(rpc, state_mgr.current, session)
                if tray_app is not None:
                    _update_tray_status(tray_app, state_mgr.current)

            # ── Sleep for the remainder of the interval ───────────────────────
            elapsed = time.monotonic() - loop_start
            sleep_time = max(0.0, UPDATE_INTERVAL - elapsed)
            time.sleep(sleep_time)
    except Exception as exc:  # pragma: no cover - defensive logging
        _log.exception("Unhandled exception — exiting: %s", exc)
        raise
    finally:
        # Log a clear exit message including whether Resolve was detected
        try:
            resolve_was_active = state_mgr.current.resolve_active
        except Exception:
            resolve_was_active = False

        if not resolve_was_active:
            _log.info("Exiting: DaVinci Resolve não detectado no sistema.")
        elif _shutdown_requested:
            _log.info("Exiting: encerramento solicitado (signal).")
        else:
            _log.info("Exiting: encerrando aplicação.")

        # ── Cleanup ───────────────────────────────────────────────────────
        _log.info("Shutting down …")
        session.pause()
        rpc.close()
        _log.info("Goodbye.")


# ── Tray status helper ────────────────────────────────────────────────────────


def _update_tray_status(tray_app, state: AppState) -> None:
    """Push the current state to the tray status label (best-effort)."""
    try:
        from config import INACTIVE_DETAILS

        if not state.resolve_active:
            tray_app.update_status(INACTIVE_DETAILS, "")
        else:
            tray_app.update_status(state.mode, state.project_name)
    except Exception as exc:
        _log.debug("Failed to update tray status: %s", exc)


# ── Entry point ───────────────────────────────────────────────────────────────


if __name__ == "__main__":
    # ── Auto-start setup (first-run, idempotent) ──────────────────────────────
    if AUTOSTART_ENABLED and not _autostart.is_enabled():
        _autostart.enable()

    # ── System tray ───────────────────────────────────────────────────────────
    # Try to launch with a tray icon.  Falls back to headless if pystray or
    # Pillow are not available.
    def _request_shutdown() -> None:
        global _shutdown_requested
        _shutdown_requested = True

    try:
        from tray import TrayApp

        tray = TrayApp(run_loop_fn=run, shutdown_callback=_request_shutdown)
        tray.start()
    except Exception as exc:
        _log.warning("Tray launch failed (%s) — running headless.", exc)
        run()
