"""Structured logging setup for DaVinciRPC."""

import logging
import sys
from typing import Optional


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_root_configured = False


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
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        _root_configured = True

    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
