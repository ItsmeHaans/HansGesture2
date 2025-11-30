# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import threading
import cv2
import time
import traceback

# Gesture / Actions
from gesture.detector import GestureDetector
from gesture.actions import GestureActions
from gesture.position import AdvancedGesture
from gesture.area import LeftAreaSelector

from services.app_launcher import AppLauncher
from services.mouse_control import MouseControl
from services.system_control import SystemControl

# Voice Feature
from services.voice_runner import run_voice_assistant, stop_voice_assistant
from voice_feature.backend_voice_chat import run_voice_chat
from voice_feature.backend_voice_timer import run_voice_timer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

gesture_thread = None
gesture_running = False

# FRAME BUFFER
last_frame = None
last_frame_lock = threading.Lock()


def set_last_frame(frame):
    global last_frame
    with last_frame_lock:
        last_frame = frame.copy() if frame is not None else None


def get_last_frame():
    with last_frame_lock:
        return last_frame.copy() if last_frame is not None else None


# =====================================================
# MJPEG STREAM
# =====================================================
def frame_streamer():
    while True:
        frame = get_last_frame()

        if frame is None:
            time.sleep(0.02)
            continue

        ret, jpeg = cv2.imencode(".jpg", frame)
        if not ret:
            time.sleep(0.02)
            continue

        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
            jpeg.tobytes() +
            b"\r\n"
        )
        time.sleep(0.02)


@app.get("/video-stream")
def video_stream():
    return StreamingResponse(
        frame_streamer(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# =====================================================
# VOICE THREAD
# =====================================================
def start_voice_thread(state):
    if state["voice_running"]:
        return False

    def _run():
        try:
            run_voice_assistant()
        except:
            traceback.print_exc()
        finally:
            state["voice_running"] = False
            state["voice_thread"] = None

    t = threading.Thread(target=_run, daemon=True)
    state["voice_thread"] = t
    state["voice_running"] = True
    t.start()

    return True


def stop_voice_thread(state):
    if not state["voice_running"]:
        return False

    try:
        stop_voice_assistant()
    except:
        pass

    t = state["voice_thread"]
    if t:
        t.join(timeout=1)

    state["voice_running"] = False
    state["voice_thread"] = None
    return True


# =====================================================
# START MAIN (Gesture loop)
# =====================================================
@app.post("/start-main")
def start_main():
    global gesture_thread, gesture_running

    if gesture_running:
        return {"status": "already_running"}

    gesture_thread = threading.Thread(target=run_gesture_loop, daemon=True)
    gesture_thread.start()
    gesture_running = True

    return {"status": "started"}


# =====================================================
# GESTURE LOOP
# =====================================================
def run_gesture_loop():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1920)
    cap.set(4, 720)

    detector = GestureDetector()
    static = GestureActions()
    motion = AdvancedGesture()
    area = LeftAreaSelector()

    launcher = AppLauncher()
    mouse = MouseControl()
    system = SystemControl()

    freehand_enabled = False
    open_start = None
    OPEN_HOLD = 3

    last_action = 0
    COOLDOWN = 0.5

    last_gesture = None
    gesture_start = None
    GESTURE_CONFIRM = 0.5

    # Voice state
    state = {
        "voice_running": False,
        "voice_thread": None
    }

    german_hold = None
    GERMAN_HOLD_TIME = 1.0

    print("[MAIN] Gesture loop started")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (1456, 783))

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)

            if results and results.multi_hand_landmarks:
                for hand in results.multi_hand_landmarks:

                    lm = hand.landmark
                    fingers = detector.get_finger_states(lm)
                    static_gesture = static.detect_static(lm)



                    # FREE-HAND OFF by PINCH
                    if static_gesture == "PINCH":
                        freehand_enabled = False
                        open_start_time = None

                    # Left area → open app
                    zone = area.detect(lm, static_gesture)
                    if zone:
                        try: launcher.run(zone)
                        except: pass

                        detector.draw_landmarks(frame, hand)
                        cv2.putText(frame, zone, (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    (0, 255, 255), 2)
                        set_last_frame(frame)
                        continue

                    # Motion gestures
                    one = motion.one_finger_up(lm)
                    two = motion.two_finger_up(lm)
                    three = motion.three_finger_up(lm)
                    scroll = motion.scroll(fingers, lm)
                    german = motion.german_three(fingers)

                    final = scroll or static_gesture
                    for g in [one, two, three, german]:
                        if g:
                            final = g

                    # Voice start
                    if final == "GERMAN_3":
                        if not state["voice_running"]:
                            if german_hold is None:
                                german_hold = time.time()

                            elapsed = time.time() - german_hold
                            cv2.putText(frame, f"VOICE {elapsed:.1f}",
                                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX,
                                        0.7, (0, 200, 255), 2)

                            if elapsed >= GERMAN_HOLD_TIME:
                                start_voice_thread(state)
                                german_hold = None
                        else:
                            german_hold = None

                        detector.draw_landmarks(frame, hand)
                        set_last_frame(frame)
                        continue
                    else:
                        german_hold = None

                    # Stop voice
                    if final == "THUMBS_UP":
                        if state["voice_running"]:
                            stop_voice_thread(state)

                        detector.draw_landmarks(frame, hand)
                        cv2.putText(frame, "THUMBS_UP", (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 120, 255), 2)
                        set_last_frame(frame)
                        continue

                    # Open hold → enable freehand
                    if static_gesture == "OPEN":
                        if not freehand_enabled:
                            if open_start is None:
                                open_start = time.time()

                            elapsed = time.time() - open_start
                            if elapsed >= OPEN_HOLD:
                                freehand_enabled = True
                        else:
                            try: mouse.move_cursor(lm)
                            except: pass
                    else:
                        if not freehand_enabled:
                            open_start = None

                    # Gesture actions
                    actionable = [
                        "FIST", "POINT", "TWO", "THREE", "FOUR",
                        "SCROLL_UP", "SCROLL_DOWN"
                    ]

                    now = time.time()

                    if final in actionable:
                        if now - last_action >= COOLDOWN:

                            if final != last_gesture:
                                gesture_start = now
                                last_gesture = final
                            else:
                                if now - gesture_start >= GESTURE_CONFIRM:

                                    try:
                                        if final == "FIST":
                                            mouse.left_click()
                                        elif final == "POINT":
                                            system.volume_up()
                                        elif final == "TWO":
                                            system.volume_down()
                                        elif final == "THREE":
                                            system.brightness_up()
                                        elif final == "FOUR":
                                            system.brightness_down()
                                        elif final == "SCROLL_UP":
                                            mouse.scroll_up()
                                        elif final == "SCROLL_DOWN":
                                            mouse.scroll_down()
                                    except:
                                        pass

                                    last_action = now

                    detector.draw_landmarks(frame, hand)
                    cv2.putText(frame, final, (10, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 0), 2)

            if state["voice_running"]:
                cv2.putText(frame, "VOICE ACTIVE", (10, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (0, 220, 180), 2)

            set_last_frame(frame)

    except Exception as e:
        print("[Gesture ERROR]", e)
        traceback.print_exc()



    finally:
        cap.release()
        if state["voice_running"]:
            stop_voice_thread(state)
        print("[MAIN] Gesture loop exited")


# =====================================================
# SYSTEM INFO ENDPOINTS
# =====================================================
system_reader = SystemControl()


@app.get("/sys/brightness")
def api_get_brightness():
    return {"percent": system_reader.get_brightness()}


@app.get("/sys/volume")
def api_get_volume():
    return {"percent": system_reader.get_volume()}


# =====================================================
# VOICE ENDPOINTS
# =====================================================
@app.post("/voice-chat")
def voice_chat_api():
    return run_voice_chat()


@app.post("/voice-timer")
def voice_timer_api():
    return run_voice_timer()


# =====================================================
# RUN SERVER
# =====================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
