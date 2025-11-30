from flask import Flask, Response
import cv2
import time

from gesture.detector import GestureDetector
from gesture.actions import GestureActions
from gesture.position import AdvancedGesture
from gesture.area import LeftAreaSelector

from services.app_launcher import AppLauncher
from services.mouse_control import MouseControl
from services.system_control import SystemControl


app = Flask(__name__)

# =============================
# INITIALIZE EVERYTHING
# =============================
cap = cv2.VideoCapture(0)

detector = GestureDetector()
static = GestureActions()
motion = AdvancedGesture()
area = LeftAreaSelector()

launcher = AppLauncher()
mouse = MouseControl()
system = SystemControl()

# FREE-HAND CONTROL
freehand_enabled = False
open_start_time = None
OPEN_HOLD_TIME = 3  # detik

# CONFIRMATION SYSTEM
gesture_start = None
last_gesture = None
GESTURE_CONFIRM_TIME = 0.5
GESTURE_COOLDOWN = 0.5
last_action_time = 0


# =============================
# STREAM FRAME TO CLIENT
# =============================
def generate_frames():
    global freehand_enabled
    global open_start_time
    global gesture_start
    global last_gesture
    global last_action_time

    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)

        if not ret:
            continue

        frame = cv2.resize(frame, (1456, 783))

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)

        if results and results.multi_hand_landmarks:
            for hand in results.multi_hand_landmarks:

                lm = hand.landmark
                fingers = detector.get_finger_states(lm)

                static_gesture = static.detect_static(lm)

                # ================================
                # DISABLE FREEHAND
                # ================================
                if static_gesture == "THUMB_UP":
                    freehand_enabled = False
                    open_start_time = None

                # ================================
                # LEFT APP LAUNCHER AREA
                # ================================
                zone = area.detect(lm, static_gesture)
                if zone:
                    launcher.run(zone)
                    detector.draw_landmarks(frame, hand)
                    cv2.putText(frame, zone, (10, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 255), 2)
                    continue

                # ================================
                # MOTION CONTROL
                # ================================
                one = motion.one_finger_up(lm)
                two = motion.two_finger_up(lm)
                three = motion.three_finger_up(lm)
                scroll = motion.scroll(fingers, lm)
                german = motion.german_three(fingers)

                final_gesture = static_gesture
                for g in [one, two, three, scroll, german]:
                    if g:
                        final_gesture = g

                # ================================
                # FREE-HAND OPEN HOLD
                # ================================
                if static_gesture == "OPEN":

                    if not freehand_enabled:
                        if open_start_time is None:
                            open_start_time = time.time()

                        elapsed = time.time() - open_start_time

                        if elapsed >= OPEN_HOLD_TIME:
                            freehand_enabled = True

                    if freehand_enabled:
                        mouse.move_cursor(lm)

                else:
                    if not freehand_enabled:
                        open_start_time = None

                # ================================
                # CONFIRMATION + COOLDOWN
                # ================================
                actionable_gestures = [
                    "FIST", "POINT", "TWO", "THREE",
                    "SCROLL_UP", "SCROLL_DOWN", "GERMAN_3"
                ]

                if final_gesture in actionable_gestures:

                    now = time.time()

                    if now - last_action_time >= GESTURE_COOLDOWN:

                        if final_gesture != last_gesture:
                            gesture_start = now
                            last_gesture = final_gesture

                        elif now - gesture_start >= GESTURE_CONFIRM_TIME:

                            if final_gesture == "FIST":
                                mouse.left_click()

                            elif final_gesture == "POINT":
                                system.volume_up()

                            elif final_gesture == "TWO":
                                system.volume_down()

                            elif final_gesture == "THREE":
                                system.brightness_down()

                            elif final_gesture == "SCROLL_UP":
                                mouse.scroll_up()

                            elif final_gesture == "SCROLL_DOWN":
                                mouse.scroll_down()

                            elif final_gesture == "GERMAN_3":
                                system.play_song_and_shutdown("services/lagu.mp3")

                            last_action_time = now

                detector.draw_landmarks(frame, hand)
                cv2.putText(frame, final_gesture, (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2)

        # ===============================
        # ENCODE FRAME FOR STREAM
        # ===============================
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


@app.route("/video")
def video():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def home():
    return "Hand Gesture Backend Running"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
