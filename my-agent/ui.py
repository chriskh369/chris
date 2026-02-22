from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# ── Colours ───────────────────────────────────────────────────────────────────
BG_DARK = "#0f0f1a"
BG_PANEL = "#1a1a2e"
BG_CARD = "#16213e"
ACCENT = "#7c3aed"
ACCENT_HOVER = "#6d28d9"
USER_BUBBLE = "#1d4ed8"
AGENT_BUBBLE = "#1e293b"
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
TEXT_ACTION = "#64748b"
BORDER = "#334155"


GLOBAL_STYLE = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {BG_CARD};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


class TitleBar(QWidget):
    """Draggable custom title bar."""

    close_clicked = pyqtSignal()
    minimise_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 12, 0)

        # Icon dot
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {ACCENT}; font-size: 10px;")
        layout.addWidget(dot)

        # Title
        title = QLabel("AI Agent")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600; margin-left: 8px;")
        layout.addWidget(title)
        layout.addStretch()

        # Minimise button
        min_btn = QPushButton("—")
        min_btn.setFixedSize(32, 32)
        min_btn.setStyleSheet(self._btn_style(TEXT_SECONDARY))
        min_btn.clicked.connect(self.minimise_clicked)
        layout.addWidget(min_btn)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(self._btn_style(TEXT_SECONDARY, hover_color="#ef4444"))
        close_btn.clicked.connect(self.close_clicked)
        layout.addWidget(close_btn)

        self.setStyleSheet(f"background-color: {BG_PANEL}; border-bottom: 1px solid {BORDER};")

    @staticmethod
    def _btn_style(color: str, hover_color: str = "#f1f5f9") -> str:
        return f"""
            QPushButton {{
                color: {color};
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.08); color: {hover_color}; }}
        """

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            window = self.window()
            delta = event.globalPosition().toPoint() - self._drag_pos
            window.move(window.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class ChatBubble(QFrame):
    """A single chat message bubble."""

    def __init__(self, text: str, role: str, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 4, 12, 4)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        if role == "user":
            label.setStyleSheet(f"""
                background: {USER_BUBBLE};
                color: #fff;
                border-radius: 14px 14px 4px 14px;
                padding: 10px 14px;
                font-size: 14px;
            """)
            outer.addStretch()
            outer.addWidget(label)

        elif role == "agent":
            label.setStyleSheet(f"""
                background: {AGENT_BUBBLE};
                color: {TEXT_PRIMARY};
                border-radius: 14px 14px 14px 4px;
                padding: 10px 14px;
                font-size: 14px;
                border: 1px solid {BORDER};
            """)
            outer.addWidget(label)
            outer.addStretch()

        elif role == "action":
            label.setStyleSheet(f"""
                color: {TEXT_ACTION};
                font-size: 12px;
                font-style: italic;
                padding: 2px 14px;
            """)
            outer.addWidget(label)
            outer.addStretch()

        elif role == "error":
            label.setStyleSheet(f"""
                background: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
                border: 1px solid rgba(239,68,68,0.3);
            """)
            outer.addWidget(label)
            outer.addStretch()


class InputBox(QTextEdit):
    """Text input that sends on Enter (Shift+Enter for newline)."""

    submit = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submit.emit()
            return
        super().keyPressEvent(event)


class ChatWindow(QMainWindow):
    """Main chat window."""

    send_message = pyqtSignal(str)
    new_chat_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(480, 700)
        self.setStyleSheet(GLOBAL_STYLE)
        self._is_busy = False
        self._build_ui()
        self._center_on_screen()

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        root.setStyleSheet(f"""
            #root {{
                background: {BG_DARK};
                border-radius: 16px;
                border: 1px solid {BORDER};
            }}
        """)
        self.setCentralWidget(root)

        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Title bar
        self._title_bar = TitleBar()
        self._title_bar.close_clicked.connect(QApplication.quit)
        self._title_bar.minimise_clicked.connect(self.showMinimized)
        vbox.addWidget(self._title_bar)

        # New chat button row
        btn_row = QWidget()
        btn_row.setStyleSheet(f"background: {BG_PANEL};")
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(12, 6, 12, 6)
        btn_layout.addStretch()

        new_btn = QPushButton("+ New Chat")
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; border-color: {ACCENT}; }}
        """)
        new_btn.clicked.connect(self._on_new_chat)
        btn_layout.addWidget(new_btn)
        vbox.addWidget(btn_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        vbox.addWidget(sep)

        # Scroll area for chat messages
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._messages_widget = QWidget()
        self._messages_widget.setStyleSheet(f"background: {BG_DARK};")
        self._messages_layout = QVBoxLayout(self._messages_widget)
        self._messages_layout.setContentsMargins(0, 12, 0, 12)
        self._messages_layout.setSpacing(4)
        self._messages_layout.addStretch()

        self._scroll.setWidget(self._messages_widget)
        vbox.addWidget(self._scroll, stretch=1)

        # Action status bar (single line, updates in-place — no bubble spam)
        self._action_bar = QLabel("")
        self._action_bar.setStyleSheet(f"""
            color: {TEXT_ACTION};
            font-size: 11px;
            font-style: italic;
            padding: 4px 14px 2px 14px;
            background: {BG_DARK};
        """)
        self._action_bar.setWordWrap(True)
        self._action_bar.hide()
        vbox.addWidget(self._action_bar)

        # Input area
        input_area = QWidget()
        input_area.setStyleSheet(f"background: {BG_PANEL}; border-top: 1px solid {BORDER};")
        input_layout = QVBoxLayout(input_area)
        input_layout.setContentsMargins(12, 10, 12, 12)
        input_layout.setSpacing(8)

        self._input = InputBox()
        self._input.setPlaceholderText("Ask me anything or give me a task…")
        self._input.setFixedHeight(80)
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_CARD};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QTextEdit:focus {{ border-color: {ACCENT}; }}
        """)
        self._input.submit.connect(self._on_send)
        input_layout.addWidget(self._input)

        send_row = QHBoxLayout()
        hint = QLabel("Shift+Enter for new line")
        hint.setStyleSheet(f"color: {TEXT_ACTION}; font-size: 11px;")
        send_row.addWidget(hint)
        send_row.addStretch()

        self._send_btn = QPushButton("Send ▶")
        self._send_btn.setFixedHeight(36)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {ACCENT_HOVER}; }}
            QPushButton:disabled {{ background: {BORDER}; color: {TEXT_ACTION}; }}
        """)
        self._send_btn.clicked.connect(self._on_send)
        send_row.addWidget(self._send_btn)
        input_layout.addLayout(send_row)

        vbox.addWidget(input_area)

        # Welcome message
        self._add_bubble("Hello! I'm your AI agent. I can control your computer, search the web, run commands, and help with anything you need. What can I do for you?", "agent")

    def _on_send(self):
        text = self._input.toPlainText().strip()
        if not text or self._is_busy:
            return
        self._input.clear()
        self._add_bubble(text, "user")
        self._set_busy(True)
        self.send_message.emit(text)

    def _on_new_chat(self):
        # Clear messages
        while self._messages_layout.count() > 1:  # keep the stretch
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_bubble("New conversation started. What can I do for you?", "agent")
        self.new_chat_requested.emit()

    def _add_bubble(self, text: str, role: str):
        bubble = ChatBubble(text, role)
        # Insert before the trailing stretch
        count = self._messages_layout.count()
        self._messages_layout.insertWidget(count - 1, bubble)
        # Scroll to bottom
        QApplication.processEvents()
        vsb = self._scroll.verticalScrollBar()
        vsb.setValue(vsb.maximum())

    def on_agent_message(self, text: str):
        self._add_bubble(text, "agent")

    def on_action(self, description: str):
        self._action_bar.setText(f"⚙ {description}")
        self._action_bar.show()

    def on_error(self, msg: str):
        self._add_bubble(msg, "error")
        self._set_busy(False)

    def on_done(self):
        self._action_bar.hide()
        self._action_bar.setText("")
        self._set_busy(False)

    def _set_busy(self, busy: bool):
        self._is_busy = busy
        self._send_btn.setEnabled(not busy)
        self._send_btn.setText("Thinking…" if busy else "Send ▶")
        self._input.setEnabled(not busy)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def toggle_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
