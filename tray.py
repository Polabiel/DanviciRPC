"""System tray icon and menu for DaVinciRPC.

Runs the main RPC update loop in a background daemon thread while the tray
icon lives in the main thread (required on Windows/macOS by pystray).

Usage::

    from tray import TrayApp
    app = TrayApp(run_loop_fn=run, shutdown_callback=request_shutdown)
    app.start()  # blocks until the user clicks "Sair"
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

from logger import get_logger

_log = get_logger("tray")


def _make_icon_image():
    """Create a simple tray icon image using Pillow.

    Returns a PIL ``Image`` object — a dark rounded square with the letter
    "D" in white, matching DaVinci Resolve's dark aesthetic.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore[import]
    except ImportError:
        _log.warning("Pillow not available — tray icon will be blank.")
        return None

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark rounded background
    margin = 4
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=12,
        fill=(30, 30, 30, 255),
    )

    # White letter "D"
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except (IOError, OSError):
        font = ImageFont.load_default()

    text = "D"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2 - bbox[0]
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    return img


class TrayApp:
    """Manages the system tray icon lifecycle.

    Parameters
    ----------
    run_loop_fn:
        Callable that implements the main RPC update loop.  It is called
        in a background daemon thread.  If the callable accepts a ``tray_app``
        keyword argument, ``self`` is passed so the loop can push status
        updates via :meth:`update_status`.
    shutdown_callback:
        Optional callable invoked when the user requests shutdown or restart
        via the tray menu.  Use this to set any stop flags in the calling
        module instead of having the tray import module internals.
    """

    def __init__(
        self,
        run_loop_fn: Callable,
        shutdown_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        self._run_loop_fn = run_loop_fn
        self._shutdown_callback = shutdown_callback
        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._icon = None
        self._status_text: str = "Iniciando…"

    # ── Public interface ──────────────────────────────────────────────────────

    def update_status(self, mode: str, project: str) -> None:
        """Update the status line shown in the tray menu.

        Args:
            mode:    Current editing page (e.g. ``"Edit"``) or ``"Inativo"``.
            project: Active project name or empty string.
        """
        if project:
            self._status_text = f"{mode} — {project}"
        else:
            self._status_text = mode
        self._refresh_menu()

    def start(self) -> None:
        """Create the tray icon and block until the user requests exit.

        The RPC loop is started in a background thread before the icon is
        shown.  This method returns when the user clicks *Sair*.
        """
        try:
            import pystray  # type: ignore[import]
        except ImportError:
            _log.error(
                "pystray is not installed — cannot show system tray icon. "
                "Running in headless mode instead."
            )
            self._worker_target()
            return

        self._start_worker()

        icon_image = _make_icon_image()
        self._icon = pystray.Icon(
            name="DaVinciRPC",
            icon=icon_image,
            title="DaVinciRPC",
            menu=self._build_menu(pystray),
        )
        _log.info("Starting tray icon.")
        self._icon.run()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_menu(self, pystray):  # type: ignore[no-untyped-def]
        """Build and return the pystray Menu object."""
        return pystray.Menu(
            pystray.MenuItem(
                lambda _: self._status_text,
                action=None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Reiniciar RPC", self._on_restart),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self._on_quit),
        )

    def _refresh_menu(self) -> None:
        """Ask pystray to redraw the menu so the status label updates."""
        if self._icon is not None:
            try:
                self._icon.update_menu()
            except Exception:
                pass  # best-effort; not critical

    def _make_worker_target(self) -> Callable[[], None]:
        """Return the callable to run in the worker thread.

        Passes ``tray_app=self`` to *run_loop_fn* when the function accepts
        that keyword argument, so the loop can push status updates without
        creating a circular import dependency.
        """
        import inspect

        try:
            sig = inspect.signature(self._run_loop_fn)
            accepts_tray = "tray_app" in sig.parameters
        except (ValueError, TypeError):
            accepts_tray = False

        if accepts_tray:
            return lambda: self._run_loop_fn(tray_app=self)
        return self._run_loop_fn

    def _start_worker(self) -> None:
        """Launch (or re-launch) the RPC loop in a background thread."""
        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._worker_target,
            daemon=True,
            name="rpc-worker",
        )
        self._worker.start()
        _log.info("RPC worker thread started.")

    def _worker_target(self) -> None:
        try:
            self._make_worker_target()()
        except Exception as exc:
            _log.exception("RPC worker thread raised an exception: %s", exc)

    def _request_shutdown(self) -> None:
        """Invoke the shutdown callback if one was provided."""
        if self._shutdown_callback is not None:
            try:
                self._shutdown_callback()
            except Exception as exc:
                _log.debug("Shutdown callback raised: %s", exc)

    def _on_restart(self, icon, item) -> None:  # noqa: ARG002
        """Menu handler: Reiniciar RPC."""
        _log.info("Restart requested via tray menu.")
        self._request_shutdown()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=5)
        self._status_text = "Reiniciando…"
        self._refresh_menu()
        self._start_worker()

    def _on_quit(self, icon, item) -> None:  # noqa: ARG002
        """Menu handler: Sair."""
        _log.info("Quit requested via tray menu.")
        self._request_shutdown()
        self._stop_event.set()
        if self._icon is not None:
            self._icon.stop()
