"""Structured logging setup for DaVinciRPC."""

import logging
import logging.handlers
import os
import sys
from typing import Optional


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_root_configured = False


def _get_log_dir() -> str:
    """Return the platform-appropriate directory for log files."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "DaVinciRPC", "logs")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Logs/DaVinciRPC")
    # Linux / other
    xdg = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(xdg, "davincirpc", "logs")


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Return a named logger.  On first call the root handler is installed.

    Args:
        name: Dotted module name (e.g. ``"resolve.detector"``).
        level: Override log level for this specific logger (optional).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    global _root_configured

    if not _root_configured:
        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        # Console handler (stdout) — present when running from a terminal or
        # during development; harmless when there is no console.
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

        # Rotating file handler — always present so the background process
        # leaves a trace even when there is no visible console.
        try:
            log_dir = _get_log_dir()
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "davincirpc.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=2 * 1024 * 1024,  # 2 MiB
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError:
            # If we cannot write logs (e.g. read-only filesystem), continue
            # without a file handler rather than crashing on startup.
            pass

        _root_configured = True

    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
