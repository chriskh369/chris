"""
AI Air Canvas - Draw in the air using hand gestures!

Gestures:
  - 1 finger (index)          -> DRAW with current color
  - 2 fingers (index+middle)  -> Switch to Green
  - 3 fingers (idx+mid+ring)  -> Switch to Red
  - 4 fingers (all no thumb)  -> Switch to Blue
  - Open palm (5 fingers)     -> ERASER
  - Fist (no fingers)         -> Pause / idle

Controls:
  - 'c' : Clear canvas
  - 'q' : Quit
  - '+'/'-' : Increase/decrease brush size
  - 's' : Save canvas as PNG
"""

import cv2
import numpy as np
import time
import os

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

# ─── Configuration ──────────────────────────────────────────────────────────
# Color hotkeys: 2 fingers → Green, 3 → Red, 4 → Blue
GESTURE_COLORS = {
    2: ("Green",  (0, 255, 0)),
    3: ("Red",    (0, 0, 255)),
    4: ("Blue",   (255, 0, 0)),
}

DEFAULT_BRUSH_SIZE = 6
MIN_BRUSH_SIZE = 2
MAX_BRUSH_SIZE = 30
BRUSH_STEP = 2
ERASER_SIZE = 40

HEADER_HEIGHT = 65
SMOOTHING_SLOW = 0.45
SMOOTHING_FAST = 0.15
SPEED_THRESHOLD = 40
DEBOUNCE_FRAMES = 3

# Detection runs every N frames; reuse last result in between
DETECT_EVERY_N = 2

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")


# ─── Hand Detector ──────────────────────────────────────────────────────────
class HandDetector:
    _CONNECTIONS = (
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20),
        (5, 9), (9, 13), (13, 17),
    )
    _TIP_IDS = frozenset((4, 8, 12, 16, 20))

    def __init__(self, detection_conf=0.45, presence_conf=0.45, tracking_conf=0.4):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Hand landmarker model not found at {MODEL_PATH}\n"
                "Download it with:\n"
                "  curl -L -o hand_landmarker.task "
                "https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
            )

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=detection_conf,
            min_hand_presence_confidence=presence_conf,
            min_tracking_confidence=tracking_conf,
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        self.landmarks = []
        self.handedness = "Right"
        self._start_time = time.time()

    def detect(self, frame):
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        ts_ms = int((time.time() - self._start_time) * 1000)
        result = self.landmarker.detect_for_video(mp_image, ts_ms)

        self.landmarks = []
        if result.hand_landmarks:
            lms = result.hand_landmarks[0]
            self.landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in lms]
            if result.handedness:
                self.handedness = result.handedness[0][0].category_name

        return self.landmarks

    def draw_hand(self, frame):
        if len(self.landmarks) < 21:
            return
        lm = self.landmarks
        for s, e in self._CONNECTIONS:
            cv2.line(frame, lm[s], lm[e], (0, 200, 0), 2)
        for i, pt in enumerate(lm):
            cv2.circle(frame, pt, 5,
                       (0, 0, 255) if i in self._TIP_IDS else (0, 255, 0), -1)

    def fingers_up(self):
        if len(self.landmarks) < 21:
            return [False] * 5
        lm = self.landmarks
        fingers = []
        # Thumb: tip(4) vs CMC(2)
        if self.handedness == "Right":
            fingers.append(lm[4][0] > lm[2][0])
        else:
            fingers.append(lm[4][0] < lm[2][0])
        # Fingers: tip vs MCP (tip - 3)
        for tip in (8, 12, 16, 20):
            fingers.append(lm[tip][1] < lm[tip - 3][1])
        return fingers

    def palm_center(self):
        if len(self.landmarks) < 21:
            return None
        lm = self.landmarks
        return (
            (lm[0][0] + lm[5][0] + lm[9][0] + lm[13][0] + lm[17][0]) // 5,
            (lm[0][1] + lm[5][1] + lm[9][1] + lm[13][1] + lm[17][1]) // 5,
        )

    def hand_bbox_size(self):
        if len(self.landmarks) < 21:
            return ERASER_SIZE // 2
        lm = self.landmarks
        ids = (0, 1, 5, 9, 13, 17)
        xs = [lm[i][0] for i in ids]
        ys = [lm[i][1] for i in ids]
        return int(max(max(xs) - min(xs), max(ys) - min(ys)) * 1.2 / 2)

    def close(self):
        self.landmarker.close()


# ─── UI (no frame.copy — draw directly) ─────────────────────────────────────
def draw_header(frame, current_color, color_name, brush_size, mode_text):
    w = frame.shape[1]
    # Semi-transparent header: darken the header region in-place
    frame[0:HEADER_HEIGHT, :] = frame[0:HEADER_HEIGHT, :] // 3

    x = 15
    cy = HEADER_HEIGHT // 2
    cv2.circle(frame, (x + 10, cy), 12, current_color, -1)
    cv2.circle(frame, (x + 10, cy), 12, (255, 255, 255), 2)
    cv2.putText(frame, color_name, (x + 30, cy + 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(frame, f"Brush: {brush_size}px", (x + 130, cy + 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    cv2.putText(frame, mode_text, (x + 300, cy + 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2)
    cv2.putText(frame, "1F:Draw  2F:Green  3F:Red  4F:Blue  5F:Erase",
                (w - 480, cy + 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (140, 140, 140), 1)


def draw_cursor(frame, pos, color, size, mode):
    if pos is None:
        return
    x, y = pos
    if mode == "draw":
        cv2.circle(frame, (x, y), size, color, 2)
        cv2.circle(frame, (x, y), 2, color, -1)
    elif mode == "erase":
        half = size // 2
        cv2.rectangle(frame, (x - half, y - half), (x + half, y + half),
                      (200, 180, 255), 2)


# ─── Main ───────────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open webcam.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 60)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    detector = HandDetector(detection_conf=0.45, presence_conf=0.45, tracking_conf=0.4)

    canvas = None
    prev_x, prev_y = 0, 0
    smooth_x, smooth_y = 0, 0
    erase_smooth_x, erase_smooth_y = 0, 0
    brush_size = DEFAULT_BRUSH_SIZE
    color_name = "Green"
    current_color = (0, 255, 0)
    mode = "idle"
    prev_mode = "idle"

    pending_gesture = 0
    gesture_frames = 0

    frame_count = 0
    fps_time = time.time()

    print("Air Canvas started!")
    print("  1F=Draw  2F=Green  3F=Red  4F=Blue  5F=Erase  Fist=Pause")
    print("Press 'q' to quit.")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            if canvas is None:
                canvas = np.zeros((h, w, 3), dtype=np.uint8)

            # Run detection every N frames, reuse last result otherwise
            frame_count += 1
            if frame_count % DETECT_EVERY_N == 0:
                detector.detect(frame)

            landmarks = detector.landmarks

            if landmarks:
                fingers = detector.fingers_up()
                ix, iy = landmarks[8]

                non_thumb_up = sum(fingers[1:])
                all_up = sum(fingers)

                # ── OPEN PALM (5 fingers) = ERASER ──────────────────────
                if all_up >= 5:
                    mode = "erase"
                    palm = detector.palm_center()
                    if palm:
                        px, py = palm
                        if prev_mode != "erase":
                            erase_smooth_x, erase_smooth_y = px, py

                        e_speed = ((px - erase_smooth_x)**2 + (py - erase_smooth_y)**2) ** 0.5
                        e_sf = SMOOTHING_SLOW if e_speed < SPEED_THRESHOLD else SMOOTHING_FAST
                        erase_smooth_x = int(erase_smooth_x * e_sf + px * (1 - e_sf))
                        erase_smooth_y = int(erase_smooth_y * e_sf + py * (1 - e_sf))

                        half = detector.hand_bbox_size()
                        cv2.rectangle(canvas,
                                      (erase_smooth_x - half, erase_smooth_y - half),
                                      (erase_smooth_x + half, erase_smooth_y + half),
                                      (0, 0, 0), -1)

                        # Eraser visual hidden — erasing still works

                    prev_x, prev_y = 0, 0
                    pending_gesture, gesture_frames = 0, 0

                # ── 1 FINGER (index only) = DRAW ────────────────────────
                elif non_thumb_up == 1 and fingers[1]:
                    mode = "draw"

                    if prev_mode != "draw":
                        smooth_x, smooth_y = ix, iy
                        prev_x, prev_y = ix, iy

                    if iy < HEADER_HEIGHT:
                        prev_x, prev_y = 0, 0
                    else:
                        if prev_x != 0 and prev_y != 0:
                            speed = ((ix - smooth_x)**2 + (iy - smooth_y)**2) ** 0.5
                            sf = SMOOTHING_SLOW if speed < SPEED_THRESHOLD else SMOOTHING_FAST
                            smooth_x = int(smooth_x * sf + ix * (1 - sf))
                            smooth_y = int(smooth_y * sf + iy * (1 - sf))
                            cv2.line(canvas, (prev_x, prev_y), (smooth_x, smooth_y),
                                     current_color, brush_size)
                            prev_x, prev_y = smooth_x, smooth_y
                        else:
                            smooth_x, smooth_y = ix, iy
                            prev_x, prev_y = ix, iy

                    draw_cursor(frame, (ix, iy), current_color, brush_size, "draw")
                    pending_gesture, gesture_frames = 0, 0

                # ── 2-4 FINGERS = COLOR SWITCH (debounced) ──────────────
                elif non_thumb_up in (2, 3, 4):
                    mode = "select"
                    prev_x, prev_y = 0, 0

                    if non_thumb_up == pending_gesture:
                        gesture_frames += 1
                    else:
                        pending_gesture = non_thumb_up
                        gesture_frames = 1

                    if gesture_frames >= DEBOUNCE_FRAMES and non_thumb_up in GESTURE_COLORS:
                        color_name, current_color = GESTURE_COLORS[non_thumb_up]
                        gesture_frames = 0

                    preview_name, preview_color = GESTURE_COLORS.get(
                        non_thumb_up, (color_name, current_color))
                    cv2.circle(frame, (ix, iy), 20, preview_color, 3)
                    cv2.putText(frame, f"{non_thumb_up}F -> {preview_name}",
                                (ix + 25, iy - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, preview_color, 2)

                # ── FIST = IDLE ─────────────────────────────────────────
                else:
                    mode = "idle"
                    prev_x, prev_y = 0, 0
                    pending_gesture, gesture_frames = 0, 0

            else:
                mode = "idle"
                prev_x, prev_y = 0, 0
                pending_gesture, gesture_frames = 0, 0

            prev_mode = mode

            # ── Merge canvas onto frame (single-pass with numpy) ──────
            mask = np.any(canvas != 0, axis=2)
            frame[mask] = canvas[mask]

            # ── UI ────────────────────────────────────────────────────
            mode_display = {
                "draw": "DRAWING",
                "erase": "ERASER",
                "select": f"SWITCH -> {color_name}",
                "idle": "SHOW HAND",
            }.get(mode, "")

            draw_header(frame, current_color, color_name, brush_size, mode_display)

            fps = 1.0 / max(time.time() - fps_time, 0.001)
            fps_time = time.time()
            cv2.putText(frame, f"FPS: {int(fps)}", (w - 120, h - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

            cv2.imshow("Air Canvas", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                canvas = np.zeros((h, w, 3), dtype=np.uint8)
                print("Canvas cleared.")
            elif key == ord('s'):
                filename = f"air_canvas_{int(time.time())}.png"
                save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                cv2.imwrite(save_path, canvas)
                print(f"Canvas saved to {save_path}")
            elif key == ord('+') or key == ord('='):
                brush_size = min(brush_size + BRUSH_STEP, MAX_BRUSH_SIZE)
            elif key == ord('-'):
                brush_size = max(brush_size - BRUSH_STEP, MIN_BRUSH_SIZE)

    finally:
        detector.close()
        cap.release()
        cv2.destroyAllWindows()
        print("Air Canvas closed.")


if __name__ == "__main__":
    main()
