"""Simple Tkinter-based log viewer for DaVinciRPC.

Run as a separate process so it doesn't conflict with pystray/tk event
loops:

    python log_viewer.py

The viewer tails the log file created by :mod:`logger` and updates
periodically.
"""

from __future__ import annotations

import os
import sys
import traceback

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import tkinter.scrolledtext as scrolledtext
except Exception:
    print("Tkinter not available. Install tkinter to use the GUI log viewer.")
    sys.exit(1)

try:
    from logger import get_log_path
except Exception:
    # Fallback: build a reasonable default path if `logger` cannot be
    # imported for any reason.
    def get_log_path():
        base = os.path.expanduser("~")
        return os.path.join(base, "DaVinciRPC", "logs", "davincirpc.log")


class LogViewer:
    def __init__(self, log_path: str | None = None, poll_interval: int = 1000):
        self.log_path = log_path or get_log_path()
        self.poll_interval = poll_interval
        self.last_size = 0

        self.root = tk.Tk()
        self.root.title("DaVinciRPC — Logs")
        self._build_ui()
        self._init_last_size()
        self._schedule_update()

    def _build_ui(self) -> None:
        self.text = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state="disabled", width=120, height=30
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Limpar", command=self.clear).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(btn_frame, text="Salvar...", command=self.save).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(btn_frame, text="Copiar", command=self.copy_all).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(btn_frame, text="Fechar", command=self.root.destroy).pack(side=tk.RIGHT, padx=4, pady=4)

    def _init_last_size(self) -> None:
        if os.path.exists(self.log_path):
            try:
                self.last_size = os.path.getsize(self.log_path)
                # Show the last N lines on startup to give context.
                with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    tail = "".join(lines[-1000:])
                    if tail:
                        self._append_text(tail)
            except Exception:
                self._append_text("Erro ao ler arquivo de log na inicialização.\n" + traceback.format_exc())

    def _append_text(self, text: str) -> None:
        self.text.configure(state="normal")
        self.text.insert(tk.END, text)
        self.text.configure(state="disabled")
        self.text.yview(tk.END)

    def _schedule_update(self) -> None:
        self.root.after(self.poll_interval, self._update)

    def _update(self) -> None:
        try:
            if not os.path.exists(self.log_path):
                self._append_text(f"Arquivo de log não encontrado: {self.log_path}\n")
                self.last_size = 0
                self._schedule_update()
                return

            size = os.path.getsize(self.log_path)
            if size < self.last_size:
                # File was rotated/truncated — read from start.
                with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                    data = f.read()
                    if data:
                        self._append_text("\n--- Arquivo de log reiniciado ---\n")
                        self._append_text(data)
            elif size > self.last_size:
                with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(self.last_size)
                    data = f.read()
                    if data:
                        self._append_text(data)

            self.last_size = size
        except Exception:
            self._append_text("Erro ao atualizar logs:\n" + traceback.format_exc())
        finally:
            self._schedule_update()

    def clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.configure(state="disabled")

    def save(self) -> None:
        try:
            path = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Log files", "*.log"), ("All files", "*.*")])
            if not path:
                return
            content = self.text.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as out:
                out.write(content)
        except Exception:
            self._append_text("Erro ao salvar arquivo:\n" + traceback.format_exc())

    def copy_all(self) -> None:
        try:
            content = self.text.get("1.0", tk.END)
            # Copy to clipboard via Tkinter API
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            # Ensure clipboard contents persist
            self.root.update()
            messagebox.showinfo("Copiado", "Logs copiados para a área de transferência.")
        except Exception:
            self._append_text("Erro ao copiar para a área de transferência:\n" + traceback.format_exc())


def main() -> None:
    viewer = LogViewer()
    try:
        viewer.root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
