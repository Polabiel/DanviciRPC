"""DaVinciRPC — main orchestration loop.

Brings together:
- DaVinci Resolve process / window detection
- DaVinci Resolve scripting API (optional)
- Discord Rich Presence updates
- Session timing
- Application state management
"""

import signal
import sys
import time

from config import UPDATE_INTERVAL, FALLBACK_PROJECT, validate as validate_config
from core.session import SessionTracker
from core.state_manager import AppState, StateManager
from discord.rpc_client import RPCClient
from logger import get_logger
from resolve.detector import detect_mode_from_window, is_resolve_running
from resolve.resolver import ResolveClient

_log = get_logger("main")

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

    project_name = resolve_client.get_project_name() if resolve_client.available else FALLBACK_PROJECT
    timeline_name = resolve_client.get_timeline_name() if resolve_client.available else None

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
        rpc.update_inactive()
        return

    details = f"{state.mode} em andamento"
    project_label = state.project_name
    if state.timeline_name:
        project_label = f"{state.project_name} — {state.timeline_name}"
    rpc_state = f"Projeto: {project_label}"

    rpc.update_active(
        details=details,
        state=rpc_state,
        start_timestamp=session.start_timestamp,
    )


# ── Main loop ──────────────────────────────────────────────────────────────────


def run() -> None:
    """Entry point for the main update loop."""
    _log.info("DaVinciRPC starting …")
    validate_config()

    rpc = RPCClient()
    resolve_client = ResolveClient()
    session = SessionTracker()
    state_mgr = StateManager()

    # Register OS signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # Attempt initial Discord connection (non-fatal if Discord is not open yet)
    rpc.connect()

    _log.info("Entering main loop (interval=%ds) …", UPDATE_INTERVAL)

    while not _shutdown_requested:
        loop_start = time.monotonic()

        resolve_active = is_resolve_running()

        # ── Session lifecycle management ──────────────────────────────────────
        if resolve_active and not session.is_active:
            if session.elapsed_seconds > 0:
                session.resume()
            else:
                session.start()

        elif not resolve_active and session.is_active:
            session.pause()

        # ── Build state and decide whether an RPC update is needed ────────────
        new_state = _build_state(resolve_client, resolve_active)
        state_changed = state_mgr.update(new_state)

        if state_changed or not rpc.connected:
            _push_rpc(rpc, state_mgr.current, session)

        # ── Sleep for the remainder of the interval ───────────────────────────
        elapsed = time.monotonic() - loop_start
        sleep_time = max(0.0, UPDATE_INTERVAL - elapsed)
        time.sleep(sleep_time)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    _log.info("Shutting down …")
    session.pause()
    rpc.close()
    _log.info("Goodbye.")


if __name__ == "__main__":
    run()
