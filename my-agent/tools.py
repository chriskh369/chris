"""
tools.py — Claude API tool schema + dispatcher.

This module is intentionally thin: it delegates all implementation to:
  • vision.py     — screen capture and encoding
  • controller.py — mouse, keyboard, and shell actions

The TOOL_DEFINITIONS list is sent verbatim to the Anthropic API so Claude
knows what functions are available. TOOL_FUNCTIONS maps each tool name to
a callable that accepts the dict of arguments Claude provides.
"""

# ── Implementation imports ────────────────────────────────────────────────────

from vision import capture_and_encode, get_screen_size

from controller import (
    click,
    double_click,
    right_click,
    move_mouse,
    scroll,
    type_text,
    press_key,
    hotkey,
    run_command,
    wait,
    list_windows,
    focus_window,
    close_duplicate_windows,
    count_windows,
)


# ── Web search (standalone — no hardware access needed) ───────────────────────

def search_web(query: str) -> str:
    """Search DuckDuckGo and return the top 5 results."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "No results found."
        lines = [
            f"{i + 1}. {r['title']}\n   {r['body']}\n   {r['href']}"
            for i, r in enumerate(results)
        ]
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search failed: {e}"


# ── Claude API tool schema ────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "take_screenshot",
        "description": (
            "Capture the current screen as an image. "
            "Use ONLY at the start of a task (to see the screen) and at the very end (to confirm the goal). "
            "Do NOT call between actions — trust run_command to execute the full sequence."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_screen_size",
        "description": "Return the primary screen resolution (width and height in pixels).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "click",
        "description": "Left-click at pixel coordinate (x, y) on the screen.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Horizontal pixel coordinate"},
                "y": {"type": "integer", "description": "Vertical pixel coordinate"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "double_click",
        "description": "Double-click at (x, y).",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "right_click",
        "description": "Right-click at (x, y) to open a context menu.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "move_mouse",
        "description": "Move the mouse cursor to (x, y) without clicking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
    },
    {
        "name": "scroll",
        "description": (
            "Scroll at position (x, y). "
            "Positive clicks = scroll up, negative clicks = scroll down."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "clicks": {
                    "type": "integer",
                    "description": "Scroll steps — positive = up, negative = down",
                },
            },
            "required": ["x", "y", "clicks"],
        },
    },
    {
        "name": "type_text",
        "description": "Type a string of text using the keyboard at the current focus.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to type"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "press_key",
        "description": (
            "Press a single key: enter, escape, tab, backspace, space, delete, "
            "home, end, pageup, pagedown, up, down, left, right, f1–f12, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key name, e.g. 'enter', 'escape'"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "hotkey",
        "description": (
            "Press a keyboard shortcut combination, e.g. ctrl+c, ctrl+v, "
            "alt+f4, win+d, ctrl+shift+esc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keys to press together, e.g. ['ctrl', 'c']",
                },
            },
            "required": ["keys"],
        },
    },
    {
        "name": "run_command",
        "description": (
            "Run a Windows shell command or a full Python automation script. "
            "Use this as the MAIN action tool — batch the entire sequence into one call. "
            "Example: python -c \"import pyautogui, pyperclip, time; ...\" "
            "Returns stdout + stderr."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "list_windows",
        "description": "List all open window titles, optionally filtered by a substring. Use to check what is currently open before opening a new app.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title_filter": {"type": "string", "description": "Optional substring to filter by (case-insensitive). Leave empty for all windows."},
            },
            "required": [],
        },
    },
    {
        "name": "count_windows",
        "description": "Count how many open windows have a title containing the given string. Use to check for duplicates before opening an app.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Substring to match in window titles"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "focus_window",
        "description": "Bring an already-open window to the foreground by partial title match. Use instead of re-opening an app that is already running.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Partial window title to match"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "close_duplicate_windows",
        "description": "Enforce single-instance policy: if more than one window matches the title, close all duplicates and keep only the first. Call this immediately if you detect multiple instances of the same app.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Partial title of the app to deduplicate (e.g. 'Chrome', 'File Explorer', 'Notepad')"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "wait",
        "description": (
            "Pause for a number of seconds (max 10) to let a page load, "
            "an animation finish, or an app to open before taking the next action."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "description": "Seconds to wait (0.5 – 10)"},
            },
            "required": ["seconds"],
        },
    },
    {
        "name": "search_web",
        "description": (
            "Search the web with DuckDuckGo and return the top 5 results "
            "(title, snippet, URL)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
]


# ── Tool dispatcher ───────────────────────────────────────────────────────────

TOOL_FUNCTIONS: dict = {
    "take_screenshot":  lambda args: capture_and_encode(),
    "get_screen_size":  lambda args: str(get_screen_size()),
    "click":            lambda args: click(args["x"], args["y"]),
    "double_click":     lambda args: double_click(args["x"], args["y"]),
    "right_click":      lambda args: right_click(args["x"], args["y"]),
    "move_mouse":       lambda args: move_mouse(args["x"], args["y"]),
    "scroll":           lambda args: scroll(args["x"], args["y"], args["clicks"]),
    "type_text":        lambda args: type_text(args["text"]),
    "press_key":        lambda args: press_key(args["key"]),
    "hotkey":           lambda args: hotkey(*args["keys"]),
    "run_command":              lambda args: run_command(args["command"]),
    "list_windows":             lambda args: list_windows(args.get("title_filter", "")),
    "count_windows":            lambda args: count_windows(args["title"]),
    "focus_window":             lambda args: focus_window(args["title"]),
    "close_duplicate_windows":  lambda args: close_duplicate_windows(args["title"]),
    "wait":                     lambda args: wait(args["seconds"]),
    "search_web":       lambda args: search_web(args["query"]),
}
