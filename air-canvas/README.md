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

```bash
pip install -r requirements.txt
python air_canvas.py
```

The `hand_landmarker.task` model file is included in this folder.

## Controls

| Key | Action |
|-----|--------|
| `c` | Clear canvas |
| `s` | Save canvas as PNG |
| `+` / `-` | Brush size (2–30px) |
| `q` | Quit |

## Stack

Python · OpenCV · MediaPipe · NumPy
