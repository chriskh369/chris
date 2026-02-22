# Chris's Projects

A collection of personal projects — AI tools, creative apps, and experiments.

---

## 🤖 my-agent — AI Computer Use Agent

Chat in natural language → the agent sees your screen → executes the task on your PC.

Powered by Claude (Haiku). The agent takes a screenshot, reasons about the task, then batches
all actions into a single Python script — no wasted frames, instant results.

**What it can do:** open apps · browse the web · manage files · type text · click anywhere ·
search DuckDuckGo · handle multi-monitor setups

**Stack:** Python · PyQt6 · Claude API · pyautogui · pynput

**Run:**
```bash
cd my-agent
pip install -r requirements.txt
pythonw main.py
```

| Control | Action |
|---------|--------|
| `Ctrl+Shift+Space` | Toggle chat window |
| Mouse to any corner | Emergency stop |

---

## ✋ air-canvas — Draw in the Air

Real-time hand gesture drawing. Your index finger is the brush — no mouse needed.

MediaPipe tracks 21 hand landmarks at 60fps. Adaptive smoothing, gesture debouncing,
color switching by finger count.

**Stack:** Python · OpenCV · MediaPipe

**Run:**
```bash
cd air-canvas
pip install -r requirements.txt
python air_canvas.py
```

| Gesture | Action |
|---------|--------|
| 1 finger | Draw |
| Open palm | Eraser |
| Fist | Pause |

---

## 📚 StudyHub — Study Management App

A Progressive Web App study organizer — offline-first, installable on phone, no server needed.

**Open:** `StudyHub App/index.html` — just open in browser, no install required

---

*Each folder is self-contained with its own README and requirements. More projects added over time.*
