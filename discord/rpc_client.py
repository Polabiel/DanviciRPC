"""Discord RPC client with automatic reconnection and exponential back-off."""

import time
from typing import Optional

from pypresence import (  # type: ignore[import-untyped]
    Presence,
    InvalidID,
    InvalidPipe,
    DiscordError,
    DiscordNotFound,
    PipeClosed,
    ConnectionTimeout,
    ResponseTimeout,
)

from config import (
    CLIENT_ID,
    LARGE_IMAGE_KEY,
    LARGE_IMAGE_TEXT,
    MAX_RECONNECT_ATTEMPTS,
    RECONNECT_BASE_DELAY,
    RECONNECT_MAX_DELAY,
    INACTIVE_DETAILS,
    INACTIVE_STATE,
)
from logger import get_logger

_log = get_logger("discord.rpc_client")


class RPCClient:
    """Manages the lifecycle of a Discord Rich Presence connection.

    All public methods are safe to call even when Discord is not running or
    the connection has been lost — they will attempt to reconnect transparently.
    """

    def __init__(self) -> None:
        self._presence: Optional[Presence] = None
        self._connected: bool = False
        self._reconnect_attempt: int = 0

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        """``True`` when the Discord IPC pipe is open."""
        return self._connected

    def connect(self) -> bool:
        """Open the IPC connection to Discord.

        Returns:
            ``True`` on success, ``False`` if Discord is not reachable.
        """
        try:
            self._presence = Presence(CLIENT_ID)
            self._presence.connect()
            self._connected = True
            self._reconnect_attempt = 0
            _log.info("Connected to Discord RPC.")
            return True
        except InvalidID as exc:
            _log.error(
                "Invalid Discord CLIENT_ID %r — check your config.py: %s",
                CLIENT_ID,
                exc,
            )
            self._connected = False
            return False
        except InvalidPipe as exc:
            _log.warning("Discord IPC pipe not found (is Discord running?): %s", exc)
            self._connected = False
            return False
        except DiscordNotFound as exc:
            _log.warning("Discord is not installed or not running: %s", exc)
            self._connected = False
            return False
        except (ConnectionTimeout, ResponseTimeout) as exc:
            _log.warning("Timed out while connecting to Discord: %s", exc)
            self._connected = False
            return False
        except ConnectionRefusedError as exc:
            _log.warning("Discord refused the connection: %s", exc)
            self._connected = False
            return False
        except OSError as exc:
            _log.warning("OS error while connecting to Discord: %s", exc)
            self._connected = False
            return False

    def update_active(
        self,
        details: str,
        state: str,
        start_timestamp: Optional[float],
    ) -> None:
        """Push an *active* presence update to Discord.

        Args:
            details: First line shown in Discord (e.g. ``"Edit em andamento"``).
            state:   Second line (e.g. ``"Projeto: MyFilm"``).
            start_timestamp: Unix timestamp used to display elapsed time.
        """
        if not self._ensure_connected():
            _log.debug("Skipped update_active: not connected to Discord")
            return

        payload: dict = {
            "details": details,
            "state": state,
            "large_image": LARGE_IMAGE_KEY,
            "large_text": LARGE_IMAGE_TEXT,
        }
        if start_timestamp is not None:
            payload["start"] = int(start_timestamp)

        _log.debug("Sending RPC active update: %s", payload)
        self._safe_update(**payload)

    def update_inactive(self) -> None:
        """Push an *inactive* presence to Discord (Resolve is closed)."""
        if not self._ensure_connected():
            _log.debug("Skipped update_inactive: not connected to Discord")
            return

        payload = dict(
            details=INACTIVE_DETAILS,
            state=INACTIVE_STATE,
            large_image=LARGE_IMAGE_KEY,
            large_text=LARGE_IMAGE_TEXT,
        )
        _log.debug("Sending RPC inactive update: %s", payload)
        self._safe_update(**payload)

    def close(self) -> None:
        """Gracefully close the Discord RPC connection."""
        if self._presence is not None and self._connected:
            try:
                self._presence.close()
                _log.info("Discord RPC connection closed.")
            except OSError as exc:
                _log.warning("Error while closing Discord RPC: %s", exc)
        self._presence = None
        self._connected = False

    # ── Private helpers ───────────────────────────────────────────────────────

    def _ensure_connected(self) -> bool:
        """Return ``True`` if already connected; otherwise attempt reconnection."""
        if self._connected:
            return True
        return self._reconnect()

    def _reconnect(self) -> bool:
        """Try to reconnect with exponential back-off.

        Returns:
            ``True`` when a connection was successfully established.
        """
        if self._reconnect_attempt >= MAX_RECONNECT_ATTEMPTS:
            _log.error(
                "Exceeded maximum reconnection attempts (%d). "
                "Will retry on next update cycle.",
                MAX_RECONNECT_ATTEMPTS,
            )
            self._reconnect_attempt = 0
            return False

        delay = min(
            RECONNECT_BASE_DELAY * (2 ** self._reconnect_attempt),
            RECONNECT_MAX_DELAY,
        )
        _log.info(
            "Reconnection attempt %d/%d in %.1fs …",
            self._reconnect_attempt + 1,
            MAX_RECONNECT_ATTEMPTS,
            delay,
        )
        time.sleep(delay)
        self._reconnect_attempt += 1

        if self.connect():
            return True
        return False

    def _safe_update(self, **kwargs: object) -> None:
        """Call :meth:`pypresence.Presence.update` with error handling."""
        if self._presence is None:
            _log.warning("Attempted RPC update with no Presence object")
            return
        try:
            _log.debug("Attempting Presence.update with payload")
            self._presence.update(**kwargs)  # type: ignore[arg-type]
            _log.debug("RPC update sent: %s", kwargs)
        except DiscordError as exc:
            _log.warning("Discord returned an error during update: %s", exc)
            self._connected = False
        except (InvalidPipe, PipeClosed) as exc:
            _log.warning("Discord pipe lost during update: %s", exc)
            self._connected = False
        except (ConnectionTimeout, ResponseTimeout) as exc:
            _log.warning("Discord update timed out: %s", exc)
            self._connected = False
        except OSError as exc:
            _log.warning("OS error during RPC update: %s", exc)
            self._connected = False
        except AttributeError as exc:
            _log.warning("Presence object in unexpected state: %s", exc)
            self._connected = False
