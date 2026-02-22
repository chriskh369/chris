"""
AI Agent — entry point.

Usage:
    python main.py

Hotkey: Ctrl+Shift+Space  →  toggle the chat window
Tray icon: left-click      →  toggle the chat window
"""

import sys
import threading
import io
import socket

import keyboard
import pystray
from PIL import Image, ImageDraw
from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout

from agent_core import AgentWorker
from config import get_api_key, save_api_key
from ui import ChatWindow

HOTKEY = "ctrl+shift+space"
_SINGLE_INSTANCE_PORT = 47291  # arbitrary local port used as a mutex


# ── API key dialog (shown if no key is found in .env) ────────────────────────

class ApiKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Agent — Setup")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Enter your Anthropic API key</b>"))
        layout.addWidget(QLabel(
            "Get yours at <a href='https://console.anthropic.com'>console.anthropic.com</a>. "
            "It will be saved locally."
        ))

        self._field = QLineEdit()
        self._field.setPlaceholderText("sk-ant-…")
        self._field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._field)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_key(self) -> str:
        return self._field.text().strip()


# ── Tray icon ─────────────────────────────────────────────────────────────────

def _make_tray_icon() -> Image.Image:
    """Generate a simple purple circle tray icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill="#7c3aed")
    draw.ellipse([18, 18, size - 18, size - 18], fill="#ffffff")
    return img


# ── Main ──────────────────────────────────────────────────────────────────────

def _acquire_single_instance_lock() -> socket.socket | None:
    """Bind to a local port. Returns the socket (hold it for app lifetime) or None if already running."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        sock.bind(("127.0.0.1", _SINGLE_INSTANCE_PORT))
        return sock
    except OSError:
        sock.close()
        return None


def main():
    # ── Single-instance guard ────────────────────────────────────────────────
    _lock_socket = _acquire_single_instance_lock()
    if _lock_socket is None:
        # Another instance is already running — show a quick Qt message and exit
        _app = QApplication(sys.argv)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(None, "AI Agent", "AI Agent is already running.\nFind it in the system tray.")
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("AI Agent")
    app.setQuitOnLastWindowClosed(False)  # keep alive in tray

    # --- API key ---
    api_key = get_api_key()
    if not api_key:
        dlg = ApiKeyDialog()
        if dlg.exec() == QDialog.DialogCode.Accepted:
            api_key = dlg.get_key()
            if api_key:
                save_api_key(api_key)
        if not api_key:
            print("No API key provided. Exiting.")
            sys.exit(1)

    # --- Agent worker ---
    worker = AgentWorker(api_key)

    # --- Chat window ---
    window = ChatWindow()
    window.send_message.connect(worker.send_message)
    window.new_chat_requested.connect(worker.reset)

    worker.message_signal.connect(window.on_agent_message)
    worker.action_signal.connect(window.on_action)
    worker.error_signal.connect(window.on_error)
    worker.done_signal.connect(window.on_done)

    window.show()

    # --- Global hotkey (runs in its own daemon thread via keyboard lib) ---
    def _toggle():
        # Must interact with Qt from main thread
        QMetaObject.invokeMethod(window, "toggle_visibility", Qt.ConnectionType.QueuedConnection)

    keyboard.add_hotkey(HOTKEY, _toggle)

    # --- System tray ---
    def _tray_show(icon, item):
        QMetaObject.invokeMethod(window, "toggle_visibility", Qt.ConnectionType.QueuedConnection)

    def _tray_quit(icon, item):
        icon.stop()
        app.quit()

    tray_icon_img = _make_tray_icon()
    menu = pystray.Menu(
        pystray.MenuItem("Open / Close", _tray_show, default=True),
        pystray.MenuItem("Quit", _tray_quit),
    )
    tray = pystray.Icon("AI Agent", tray_icon_img, "AI Agent", menu)

    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    # --- Run Qt event loop ---
    exit_code = app.exec()

    keyboard.unhook_all()
    tray.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
