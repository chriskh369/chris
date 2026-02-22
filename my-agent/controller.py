"""
controller.py — Action execution module with hardware fail-safe.

Responsibilities:
  - Translate AI-issued (x, y) coordinates into physical mouse events
  - Simulate keyboard input (typewrite, press, hotkey)
  - Run shell commands
  - Monitor mouse position via pynput and abort if the user moves the cursor
    to any corner of the screen (fail-safe kill switch)

FAIL-SAFE:
  Move the mouse to any corner of the screen (top-left, top-right,
  bottom-left, or bottom-right) to immediately abort the running task.
  A corner is defined as within CORNER_PX pixels of the screen edge.
"""

import ctypes
import subprocess
import threading
import time

import pyautogui
import pygetwindow as gw
from pynput import mouse as _pynput_mouse

# ── DPI awareness ─────────────────────────────────────────────────────────────
# Tell Windows this process is per-monitor DPI-aware so pyautogui coordinates
# match the physical pixels in screenshots (fixes coordinate mismatch on scaled
# displays, e.g. 150% scaling on a 4K monitor).
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()   # fallback for older Windows
    except Exception:
        pass

# We handle our own fail-safe via pynput — disable pyautogui's built-in one
# so it never misinterprets valid coordinates as a fail-safe trigger
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0   # we manage our own timing

CORNER_PX = 10       # pixels from edge that trigger abort
MOVE_DURATION = 0.05 # near-instant cursor glide
TYPE_INTERVAL = 0.01 # fastest keystroke cadence
POST_ACTION_PAUSE = 0.02  # minimal OS registration gap


def _px(value) -> int:
    """Safely convert any coordinate value to int.
    Handles: '436, 14', '436 14', '436.0', 436, 436.0
    When a string contains two numbers (e.g. '435 14'), takes the first one.
    """
    if isinstance(value, str):
        value = value.replace(",", "").strip().split()[0]
    return int(round(float(value)))


# ── Abort mechanism ───────────────────────────────────────────────────────────

class AbortedError(RuntimeError):
    """Raised when the fail-safe is triggered mid-task."""


_abort_event = threading.Event()


def is_aborted() -> bool:
    return _abort_event.is_set()


def reset_abort() -> None:
    """Clear the abort flag. Call this at the start of each new user message."""
    _abort_event.clear()


def check_abort() -> None:
    """Raise AbortedError if the fail-safe has been triggered."""
    if _abort_event.is_set():
        raise AbortedError("Task aborted — mouse moved to a screen corner.")


# ── Fail-safe listener ────────────────────────────────────────────────────────

class FailSafeListener:
    """
    Runs a pynput mouse listener in a daemon thread.
    When the cursor enters any screen corner, the abort event is set.
    """

    def __init__(self):
        self._listener: _pynput_mouse.Listener | None = None

    def start(self) -> None:
        self._listener = _pynput_mouse.Listener(on_move=self._on_move)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    @staticmethod
    def _on_move(x: int, y: int) -> None:
        w, h = pyautogui.size()
        cp = CORNER_PX
        in_corner = (
            (x <= cp and y <= cp)           # top-left
            or (x >= w - cp and y <= cp)    # top-right
            or (x <= cp and y >= h - cp)    # bottom-left
            or (x >= w - cp and y >= h - cp)  # bottom-right
        )
        if in_corner:
            _abort_event.set()


# ── Mouse actions ─────────────────────────────────────────────────────────────

def _glide_to(x, y) -> None:
    """Visibly slide the cursor to pixel (x, y) over MOVE_DURATION seconds."""
    pyautogui.moveTo(_px(x), _px(y), duration=MOVE_DURATION)


def click(x, y) -> str:
    """Glide the cursor to (x, y), then left-click at those exact coordinates."""
    check_abort()
    x, y = _px(x), _px(y)
    _glide_to(x, y)
    check_abort()
    pyautogui.click(x, y)
    time.sleep(POST_ACTION_PAUSE)
    return f"Clicked at ({x}, {y})"


def double_click(x, y) -> str:
    """Glide to (x, y) and double-click at those exact coordinates."""
    check_abort()
    x, y = _px(x), _px(y)
    _glide_to(x, y)
    check_abort()
    pyautogui.doubleClick(x, y)
    time.sleep(POST_ACTION_PAUSE)
    return f"Double-clicked at ({x}, {y})"


def right_click(x, y) -> str:
    """Glide to (x, y) and right-click at those exact coordinates."""
    check_abort()
    x, y = _px(x), _px(y)
    _glide_to(x, y)
    check_abort()
    pyautogui.rightClick(x, y)
    time.sleep(POST_ACTION_PAUSE)
    return f"Right-clicked at ({x}, {y})"


def move_mouse(x, y) -> str:
    """Glide the cursor to (x, y) without clicking."""
    check_abort()
    _glide_to(_px(x), _px(y))
    time.sleep(POST_ACTION_PAUSE)
    return f"Moved mouse to ({x}, {y})"


def scroll(x, y, clicks) -> str:
    """Glide to (x, y), then scroll."""
    check_abort()
    x, y, clicks = _px(x), _px(y), int(round(float(str(clicks).replace(",", "").strip())))
    _glide_to(x, y)
    check_abort()
    pyautogui.scroll(clicks, x=x, y=y)
    time.sleep(POST_ACTION_PAUSE)
    direction = "up" if clicks > 0 else "down"
    return f"Scrolled {direction} {abs(clicks)} clicks at ({x}, {y})"


# ── Keyboard actions ──────────────────────────────────────────────────────────

def type_text(text: str) -> str:
    """Paste text via clipboard — immune to keyboard layout (Hebrew, Arabic, etc.)."""
    check_abort()
    import pyperclip
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(POST_ACTION_PAUSE)
    return f"Typed: {text!r}"


def press_key(key: str) -> str:
    check_abort()
    pyautogui.press(key)
    time.sleep(POST_ACTION_PAUSE)
    return f"Pressed key: {key}"


def hotkey(*keys: str) -> str:
    check_abort()
    pyautogui.hotkey(*keys)
    time.sleep(POST_ACTION_PAUSE)
    return f"Pressed hotkey: {'+'.join(keys)}"


# ── Wait ──────────────────────────────────────────────────────────────────────

def wait(seconds: float) -> str:
    """Pause execution for `seconds` (max 10) so a page or animation can load."""
    check_abort()
    seconds = min(float(seconds), 10.0)
    time.sleep(seconds)
    return f"Waited {seconds:.1f} s"


# ── Window management ─────────────────────────────────────────────────────────

def list_windows(title_filter: str = "") -> str:
    """Return titles of all open windows, optionally filtered by substring."""
    check_abort()
    try:
        windows = gw.getAllTitles()
        windows = [w for w in windows if w.strip()]
        if title_filter:
            windows = [w for w in windows if title_filter.lower() in w.lower()]
        return "\n".join(windows) if windows else "(no matching windows)"
    except Exception as e:
        return f"Error listing windows: {e}"


def focus_window(title: str) -> str:
    """Bring the first window whose title contains `title` to the foreground."""
    check_abort()
    try:
        matches = gw.getWindowsWithTitle(title)
        if not matches:
            return f"No window found with title containing '{title}'"
        win = matches[0]
        win.activate()
        time.sleep(0.3)
        return f"Focused: {win.title}"
    except Exception as e:
        return f"Error focusing window: {e}"


def close_duplicate_windows(title: str) -> str:
    """
    Enforce single-instance policy.
    If more than one window matches `title`, close all but the first (oldest).
    Returns a summary of what was closed.
    """
    check_abort()
    try:
        matches = gw.getWindowsWithTitle(title)
        if len(matches) <= 1:
            return f"OK — only {len(matches)} window(s) found for '{title}', nothing to close."
        closed = []
        for win in matches[1:]:   # keep the first, close the rest
            try:
                win.close()
                time.sleep(0.3)
                closed.append(win.title)
            except Exception as e:
                closed.append(f"(failed to close '{win.title}': {e})")
        return f"Closed {len(closed)} duplicate(s): {', '.join(closed)}"
    except Exception as e:
        return f"Error enforcing single instance: {e}"


def count_windows(title: str) -> str:
    """Return the number of open windows whose title contains `title`."""
    check_abort()
    try:
        matches = gw.getWindowsWithTitle(title)
        return str(len(matches))
    except Exception as e:
        return f"Error counting windows: {e}"


# ── Shell ─────────────────────────────────────────────────────────────────────

def run_command(command: str) -> str:
    """Execute a Windows shell command and return stdout + stderr (max 60 s)."""
    check_abort()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout + result.stderr).strip()
        return output[:3000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 60 seconds."
    except Exception as e:
        return f"Error running command: {e}"
