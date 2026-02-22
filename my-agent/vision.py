"""
vision.py — Perception / screen-capture module.

Responsibilities:
  - Capture a screenshot of the primary monitor
  - Compress and encode it as Base64 PNG for the Anthropic API
"""

import base64
import io

import pyautogui
from PIL import Image


def capture_screenshot() -> Image.Image:
    """Return a PIL Image of the entire primary monitor."""
    return pyautogui.screenshot()


def encode_to_base64(image: Image.Image) -> str:
    """Compress a PIL Image to PNG and return a Base64-encoded string."""
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def capture_and_encode() -> str:
    """Capture the screen and return it as a Base64 PNG string (one-liner helper)."""
    return encode_to_base64(capture_screenshot())


def get_screen_size() -> dict:
    """Return the primary screen resolution as {width, height}."""
    w, h = pyautogui.size()
    return {"width": w, "height": h}
