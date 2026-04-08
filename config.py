"""Central configuration for DaVinciRPC."""

import logging
import os

# ── Discord ──────────────────────────────────────────────────────────────────
# Override by setting the DISCORD_CLIENT_ID environment variable.
# The placeholder below is intentionally invalid so Discord will reject the
# connection and the validate() call below will emit a clear error message.
CLIENT_ID: str = os.environ.get("DISCORD_CLIENT_ID", "REPLACE_WITH_YOUR_CLIENT_ID")

# ── Polling ───────────────────────────────────────────────────────────────────
UPDATE_INTERVAL: int = int(os.environ.get("UPDATE_INTERVAL", "15"))  # seconds

# ── Feature flags ─────────────────────────────────────────────────────────────
ENABLE_RESOLVE_API: bool = os.environ.get("ENABLE_RESOLVE_API", "true").lower() == "true"

# ── Reconnection ──────────────────────────────────────────────────────────────
MAX_RECONNECT_ATTEMPTS: int = 5
RECONNECT_BASE_DELAY: float = 2.0   # seconds — base for exponential backoff
RECONNECT_MAX_DELAY: float = 60.0   # seconds — ceiling for backoff

# ── Process names ─────────────────────────────────────────────────────────────
RESOLVE_PROCESS_WINDOWS: str = "Resolve.exe"
RESOLVE_PROCESS_LINUX: str = "resolve"

# ── Window title → display mode mapping ──────────────────────────────────────
WINDOW_MODE_MAP: dict[str, str] = {
    "color": "Color Grading",
    "cut": "Cut",
    "edit": "Edit",
    "fusion": "Fusion",
    "fairlight": "Audio",
}

# ── Discord asset key ─────────────────────────────────────────────────────────
LARGE_IMAGE_KEY: str = os.environ.get("LARGE_IMAGE_KEY", "resolve")
LARGE_IMAGE_TEXT: str = "DaVinci Resolve"

# ── Fallback labels ───────────────────────────────────────────────────────────
FALLBACK_MODE: str = "Idle"
FALLBACK_PROJECT: str = "Nenhum projeto"
INACTIVE_DETAILS: str = "Inativo"
INACTIVE_STATE: str = "DaVinci Resolve fechado"


def validate() -> None:
    """Emit clear warnings for missing critical environment variables.

    Called once at startup so operators see the problem immediately instead of
    discovering it from a cryptic connection-refused error later.
    """
    _log = logging.getLogger("config")
    if not os.environ.get("DISCORD_CLIENT_ID"):
        _log.error(
            "DISCORD_CLIENT_ID environment variable is not set. "
            "The application will not connect to Discord. "
            "Export DISCORD_CLIENT_ID before running."
        )
    elif CLIENT_ID == "REPLACE_WITH_YOUR_CLIENT_ID":
        _log.error(
            "DISCORD_CLIENT_ID is still set to the placeholder value. "
            "Set it to your actual Discord Application ID."
        )
    if not os.environ.get("LARGE_IMAGE_KEY"):
        _log.info(
            "LARGE_IMAGE_KEY is not set — using default value %r.", LARGE_IMAGE_KEY
        )
