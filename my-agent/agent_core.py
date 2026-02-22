"""
agent_core.py — Reasoning loop.

The AgentWorker thread implements the full perception → reasoning → action cycle:

  1. User sends a message
  2. Thread wakes up, clears the abort flag
  3. Reasoning loop:
       a. Send conversation history + tool schema to Claude
       b. If Claude calls a tool  → execute it via tools.py (which delegates to
          vision.py or controller.py) → feed result back → repeat
       c. If Claude returns text  → emit to UI → done
  4. Any AbortedError (fail-safe triggered) surfaces as a red error bubble in the UI
"""

import anthropic
from PyQt6.QtCore import QThread, pyqtSignal

from controller import AbortedError, FailSafeListener, reset_abort
from tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS

SYSTEM_PROMPT = """You are an autonomous Windows 11 AI agent on an i7-14700KF / RTX system.
You PLAN silently then ACT immediately. Never ask permission between steps. Never say "I will now..." and wait.

════ EXECUTION MODEL ════
1. THINK: Silently form the complete plan.
2. ACT: Run the full sequence as one uninterrupted flow.
3. VERIFY: ONE final screenshot to confirm success.

════ GOLDEN RULE: ONE run_command CALL PER TASK ════
Batch the ENTIRE sequence into a single Python script. Example:

  run_command('python -c "
import pyautogui, pyperclip, time
pyautogui.PAUSE = 0.02
pyperclip.copy(\'https://youtube.com/results?search_query=jjk\')
pyautogui.hotkey(\'ctrl\', \'t\'); time.sleep(0.5)
pyautogui.hotkey(\'ctrl\', \'l\'); time.sleep(0.2)
pyautogui.hotkey(\'ctrl\', \'v\'); time.sleep(0.1)
pyautogui.press(\'enter\'); time.sleep(2)
"')

════ SCREENSHOT RULE ════
• ONE screenshot at the start (see current state)
• ONE screenshot at the end (confirm goal achieved)
• ZERO screenshots in between — trust the code

════ COORDINATE SAFETY ════
Inside run_command scripts, always sanitize coordinates before use:
  x = int(float(str(raw_x).replace(\',\',\'\').split()[0]))
  y = int(float(str(raw_y).replace(\',\',\'\').split()[0]))

════ WINDOW RULES ════
• count_windows('App') → 0: open it | 1: focus_window | >1: close_duplicate_windows
• Window with left < 0 is on secondary monitor (invisible to screenshots). Move it:
  run_command('python -c "import pygetwindow as g; w=g.getWindowsWithTitle(\\'Chrome\\')[0]; w.restore(); w.moveTo(0,0); w.maximize()"')

════ TEXT INPUT ════
Always use pyperclip.copy(text) + ctrl+v. Never pyautogui.write(). Bypasses Hebrew keyboard.

════ FILE OPERATIONS ════
Write: run_command('python -c "open(r\'C:\\\\Users\\\\User\\\\Desktop\\\\out.txt\',\'w\').write(\'content\')"')
Read:  run_command('type "C:\\\\path\\\\file.txt"')
Find:  run_command('dir /s /b "C:\\\\Users\\\\User" 2>nul | findstr /i resume')

FAIL-SAFE: mouse to any screen corner = immediate abort."""

MAX_TOOL_ITERATIONS = 25  # enough to finish any real task


class AgentWorker(QThread):
    message_signal = pyqtSignal(str)  # Final text response from Claude
    action_signal  = pyqtSignal(str)  # Per-tool status shown in the UI
    error_signal   = pyqtSignal(str)  # Error / abort messages
    done_signal    = pyqtSignal()     # Emitted when the loop exits (success or error)

    def __init__(self, api_key: str, parent=None):
        super().__init__(parent)
        self.client  = anthropic.Anthropic(api_key=api_key)
        self.history: list[dict] = []
        self._user_message = ""

        # Start the fail-safe mouse listener immediately
        self._fail_safe = FailSafeListener()
        self._fail_safe.start()

    # ── Public API ────────────────────────────────────────────────────────────

    def send_message(self, message: str) -> None:
        """Queue a user message and start the worker thread."""
        reset_abort()                  # clear any previous abort flag
        self._user_message = message
        if not self.isRunning():
            self.start()

    def reset(self) -> None:
        """Clear the conversation history (new chat)."""
        self.history = []

    # ── Thread entry point ────────────────────────────────────────────────────

    def run(self) -> None:
        try:
            self._reasoning_loop(self._user_message)
        except AbortedError:
            self.error_signal.emit("⛔ Aborted — mouse moved to a screen corner.")
        except Exception as e:
            self.error_signal.emit(f"Agent error: {e}")
        finally:
            self.done_signal.emit()

    # ── Reasoning loop ────────────────────────────────────────────────────────

    def _reasoning_loop(self, user_message: str) -> None:
        """
        Perception → Reasoning → Action cycle.

        Step 1: Append the user's message to the conversation history.
        Step 2: Send history + tool schema to Claude.
        Step 3a: If Claude calls tools → execute each → append results → repeat.
        Step 3b: If Claude responds with text → emit it → done.
        """
        self.history.append({"role": "user", "content": user_message})

        for _ in range(MAX_TOOL_ITERATIONS):
            # ── Step 2: Reasoning ─────────────────────────────────────────────
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.history,
            )

            self.history.append({"role": "assistant", "content": response.content})

            # ── Step 3b: Final text response ──────────────────────────────────
            if response.stop_reason == "end_turn":
                text_parts = [b.text for b in response.content if hasattr(b, "text")]
                final_text = "\n".join(text_parts).strip()
                if final_text:
                    self.message_signal.emit(final_text)
                return

            # ── Step 3a: Tool execution ───────────────────────────────────────
            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    self.action_signal.emit(self._describe(block.name, block.input))
                    result = self._execute(block.name, block.input)

                    # Screenshots are returned as image content blocks
                    if block.name == "take_screenshot":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": result,
                                    },
                                }
                            ],
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })

                self.history.append({"role": "user", "content": tool_results})
                continue

            self.error_signal.emit(f"Unexpected stop reason: {response.stop_reason}")
            return

        self.error_signal.emit(
            "Reached the maximum number of steps. The task may be incomplete."
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _execute(self, name: str, args: dict):
        fn = TOOL_FUNCTIONS.get(name)
        if fn is None:
            return f"Unknown tool: {name}"
        return fn(args)   # AbortedError propagates up naturally

    @staticmethod
    def _describe(name: str, args: dict) -> str:
        return {
            "take_screenshot": "Taking screenshot…",
            "get_screen_size": "Getting screen size…",
            "click":           f"Clicking at ({args.get('x')}, {args.get('y')})",
            "double_click":    f"Double-clicking at ({args.get('x')}, {args.get('y')})",
            "right_click":     f"Right-clicking at ({args.get('x')}, {args.get('y')})",
            "move_mouse":      f"Moving mouse to ({args.get('x')}, {args.get('y')})",
            "scroll":          f"Scrolling {args.get('clicks', 0):+d} at ({args.get('x')}, {args.get('y')})",
            "type_text":       f"Typing: {str(args.get('text', ''))[:40]}",
            "press_key":       f"Pressing key: {args.get('key')}",
            "hotkey":          f"Hotkey: {'+'.join(args.get('keys', []))}",
            "run_command":             f"Running: {str(args.get('command', ''))[:60]}",
            "list_windows":            f"Listing windows (filter: '{args.get('title_filter', 'all')}')",
            "count_windows":           f"Counting windows: '{args.get('title', '')}'",
            "focus_window":            f"Focusing window: '{args.get('title', '')}'",
            "close_duplicate_windows": f"Closing duplicates of: '{args.get('title', '')}'",
            "wait":                    f"Waiting {args.get('seconds', '?')} s…",
            "search_web":      f"Searching: {str(args.get('query', ''))[:60]}",
        }.get(name, f"Using tool: {name}")
