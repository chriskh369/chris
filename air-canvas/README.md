# ✋ Air Canvas — Draw in the Air

Real-time hand gesture drawing using your webcam. Your index finger is the brush — no mouse needed.

## How It Works

MediaPipe tracks 21 hand landmarks at 60fps. Finger count maps to actions.
Adaptive smoothing adjusts based on hand speed (slow hand = more smoothing).
Gesture debouncing uses a 3-frame validation window to prevent accidental switches.

| Gesture | Action |
|---------|--------|
| 1 finger (index) | ✏️ Draw |
| 2 fingers | 🟢 Switch to Green |
| 3 fingers | 🔴 Switch to Red |
| 4 fingers | 🔵 Switch to Blue |
| Open palm | 🧽 Eraser |
| Fist | ⏸️ Pause |

## Setup

**Step 1 — Make sure Python is installed**
Download from [python.org](https://www.python.org/downloads/) — check "Add Python to PATH" during install.

**Step 2 — Clone & install**

```bash
git clone https://github.com/chriskh369/chris.git
cd chris/air-canvas
python -m pip install -r requirements.txt
```

> On Windows PowerShell, use `python -m pip` instead of `pip` directly.

**Step 3 — Run**

```bash
python air_canvas.py
```

The `hand_landmarker.task` model file is included — no extra downloads needed.

## Controls

| Key | Action |
|-----|--------|
| `c` | Clear canvas |
| `s` | Save canvas as PNG |
| `+` / `-` | Brush size (2–30px) |
| `q` | Quit |

## Stack

Python · OpenCV · MediaPipe · NumPy
