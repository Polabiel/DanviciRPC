"""Central configuration for DaVinciRPC."""

import os

# ── Discord ──────────────────────────────────────────────────────────────────
CLIENT_ID: str = os.environ.get("DISCORD_CLIENT_ID", "1234567890123456789")

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
LARGE_IMAGE_KEY: str = "resolve"
LARGE_IMAGE_TEXT: str = "DaVinci Resolve"

# ── Fallback labels ───────────────────────────────────────────────────────────
FALLBACK_MODE: str = "Idle"
FALLBACK_PROJECT: str = "Nenhum projeto"
INACTIVE_DETAILS: str = "Inativo"
INACTIVE_STATE: str = "DaVinci Resolve fechado"
