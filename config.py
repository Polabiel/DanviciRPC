"""Central configuration for DaVinciRPC."""

import logging
import os

# Auto-load environment variables from a .env file if python-dotenv is available.
# This allows running the project locally using a .env file without exporting vars.
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore

    _dotenv_path = find_dotenv()
    if _dotenv_path:
        load_dotenv(_dotenv_path)
except ImportError:
    # python-dotenv is optional; continue without loading a .env file.
    pass
except Exception as exc:
    logging.getLogger("config").warning(
        "Failed to load environment variables from .env: %s", exc
    )

# ── Discord ───────────────────────────────────────────────────────────────────
# Default client ID is bundled so the app works out-of-the-box.
# Can be overridden by setting the DISCORD_CLIENT_ID environment variable.
CLIENT_ID: str = os.environ.get("DISCORD_CLIENT_ID", "1491285498361020626")

# ── Polling ───────────────────────────────────────────────────────────────────
UPDATE_INTERVAL: int = int(os.environ.get("UPDATE_INTERVAL", "15"))  # seconds

# ── Feature flags ─────────────────────────────────────────────────────────────
# Disable Resolve API by default to avoid importing native DaVinciResolveScript
# on systems where Resolve is not installed or its Python modules may crash.
ENABLE_RESOLVE_API: bool = os.environ.get("ENABLE_RESOLVE_API", "false").lower() == "true"

# ── Auto-start ────────────────────────────────────────────────────────────────
# Register the app to launch automatically on system login (enabled by default).
# Can be disabled by setting AUTOSTART_ENABLED=false in the environment.
AUTOSTART_ENABLED: bool = os.environ.get("AUTOSTART_ENABLED", "true").lower() == "true"

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
# Default key is bundled. Can be overridden via the LARGE_IMAGE_KEY env var.
LARGE_IMAGE_KEY: str = os.environ.get("LARGE_IMAGE_KEY", "resolve")
LARGE_IMAGE_TEXT: str = "DaVinci Resolve"

# ── Fallback labels ───────────────────────────────────────────────────────────
FALLBACK_MODE: str = "Idle"
FALLBACK_PROJECT: str = "Nenhum projeto"
INACTIVE_DETAILS: str = "Inativo"
INACTIVE_STATE: str = "DaVinci Resolve fechado"


def validate() -> None:
    """Log informational messages about the active configuration at startup."""
    _log = logging.getLogger("config")
    _log.info("Configuration loaded — UPDATE_INTERVAL=%ds", UPDATE_INTERVAL)
    _log.info("ENABLE_RESOLVE_API=%s", ENABLE_RESOLVE_API)
    _log.info("AUTOSTART_ENABLED=%s", AUTOSTART_ENABLED)
