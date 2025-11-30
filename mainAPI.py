import cv2
import time
import threading
import traceback

from ui import GestureUI
from gesture.detector import GestureDetector
from gesture.actions import GestureActions
from gesture.position import AdvancedGesture
from gesture.area import LeftAreaSelector

from services.app_launcher import AppLauncher
from services.mouse_control import MouseControl
from services.system_control import SystemControl

# VOICE RUNNER
from services.voice_runner import run_voice_assistant, stop_voice_assistant


# =====================================================
# FASTAPI SERVER (API)
# =====================================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# GLOBAL STATE for API & Gesture
GLOBAL_STATE = {
    "voice_running": False,
    "voice_thread": None,
    "last_gesture": None,
}


# =====================================================
# VOICE THREAD CONTROLLER
# =====================================================
def start_voice_thread():
    if GLOBAL_STATE["voice_running"]:
        return False

    def _runner():
        try:
            run_voice_assistant()
        except:
            traceback.print_exc()
        finally:
            GLOBAL_STATE["voice_running"] = False
            GLOBAL_STATE["voice_thread"] = None
            print("[VoiceThread] EXITED")

    t = threading.Thread(target=_runner, daemon=True)
    GLOBAL_STATE["voice_thread"] = t
    GLOBAL_STATE["voice_running"] = True
    t.start()
    print("[VoiceThread] STARTED")
    return True


def stop_voice_thread():
    if not GLOBAL_STATE["voice_running"]:
        return False

    try:
        stop_voice_assistant()
    except:
        pass

    t = GLOBAL_STATE["voice_thread"]
    if t:
        t.join(timeout=1)

    GLOBAL_STATE["voice_running"] = False
    GLOBAL_STATE["voice_thread"] = None
    print("[VoiceThread] STOPPED")
    return True


# =====================================================
# API ENDPOINTS
# =====================================================

@app.get("/voice/start")
def api_voice_start():
    ok = start_voice_thread()
    return {"success": ok, "voice_running": GLOBAL_STATE["voice_running"]}

@app.get("/voice/stop")
def api_voice_stop():
    ok = stop_voice_thread()
    return {"success": ok, "voice_running": GLOBAL_STATE["voice_running"]}

@app.get("/gesture/state")
def api_gesture_state():
    return {
        "gesture": GLOBAL_STATE["last_gesture"],
        "voice_running": GLOBAL_STATE["voice_running"]
    }

@app.get("/system/volume_up")
def api_volume_up():
    SystemControl().volume_up()
    return {"status": "ok"}

@app.get("/system/volume_down")
def api_volume_down():
    SystemControl().volume_down()
    return {"status": "ok"}

@app.get("/system/shutdown")
def api_shutdown():
    SystemControl().shutdown()
    return {"status": "shutting down"}



# =====================================================
# RUN FASTAPI IN SEPARATE THREAD
# =====================================================
def start_api_server():
    def _run():
        uvicorn.run(app, host="0.0.0.0", port=8000)
    threading.Thread(target=_run, daemon=True).start()


# =====================================================
# MAIN GESTURE APPLICATION
# =====================================================
def main():
    # START API SERVER
    start_api_server()
    print("[API] Server running on http://localhost:8000")

    cap = cv2.VideoCapture(0)
    cap.set(3, 1920)
    cap.set(4, 720)

    ui = GestureUI()
    detector = GestureDetector()
    static = GestureActions()
    motion = AdvancedGesture()
    area = LeftAreaSelector()

    launcher = AppLauncher()
    mouse = MouseControl()
    system = SystemControl()

    freehand_enabled = False
    open_start_time = None
    OPEN_HOLD_TIME = 3

    gesture_start = None
    last_gesture = None
    GESTURE_CONFIRM = 0.5
    COOLDOWN = 0.5
    last_action_time = 0

    german_hold_start = None
    GERMAN_HOLD = 1.0

    while True:
        try:
            if ui.check_quit():
                break

            ret, frame = cap.read()
            if not ret or frame is None:
                break

            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (1456, 783))

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)

            if results and results.multi_hand_landmarks:
                for hand in results.multi_hand_landmarks:

                    lm = hand.landmark
                    fingers = detector.get_finger_states(lm)
                    static_gesture = static.detect_static(lm)

                    # SAVE last gesture to API state
                    GLOBAL_STATE["last_gesture"] = static_gesture

                    # FREE-HAND OFF by PINCH
                    if static_gesture == "PINCH":
                        freehand_enabled = False
                        open_start_time = None

                    # AREA SELECTION
                    zone = area.detect(lm, static_gesture)
                    if zone:
                        try:
                            launcher.run(zone)
                        except:
                            pass
                        detector.draw_landmarks(frame, hand)
                        continue

                    # MOTION
                    one = motion.one_finger_up(lm)
                    two = motion.two_finger_up(lm)
                    three = motion.three_finger_up(lm)
                    scroll = motion.scroll(fingers, lm)
                    german = motion.german_three(fingers)

                    if scroll:
                        final_gesture = scroll
                    else:
                        final_gesture = static_gesture
                        for g in [one, two, three, german]:
                            if g:
                                final_gesture = g

                    GLOBAL_STATE["last_gesture"] = final_gesture

                    # GERMAN 3 — start voice
                    if final_gesture == "GERMAN_3":
                        if not GLOBAL_STATE["voice_running"]:
                            if german_hold_start is None:
                                german_hold_start = time.time()
                            elapsed = time.time() - german_hold_start
                            if elapsed >= GERMAN_HOLD:
                                start_voice_thread()
                                german_hold_start = None
                        else:
                            german_hold_start = None

                        detector.draw_landmarks(frame, hand)
                        ui.draw_frame(frame)
                        continue

                    else:
                        german_hold_start = None

                    # THUMB UP — stop voice
                    if final_gesture == "THUMBS_UP":
                        if GLOBAL_STATE["voice_running"]:
                            stop_voice_thread()
                        detector.draw_landmarks(frame, hand)
                        ui.draw_frame(frame)
                        continue

                    # FREE HAND HOLD
                    if static_gesture == "OPEN":
                        if not freehand_enabled:
                            if open_start_time is None:
                                open_start_time = time.time()
                            if time.time() - open_start_time >= OPEN_HOLD_TIME:
                                freehand_enabled = True
                        if freehand_enabled:
                            mouse.move_cursor(lm)
                    else:
                        if not freehand_enabled:
                            open_start_time = None

                    actionable = [
                        "FIST", "POINT", "TWO", "THREE", "FOUR",
                        "SCROLL_UP", "SCROLL_DOWN"
                    ]

                    now = time.time()

                    if final_gesture in actionable:
                        if now - last_action_time >= COOLDOWN:

                            if final_gesture != last_gesture:
                                gesture_start = now
                                last_gesture = final_gesture
                            else:
                                if now - gesture_start >= GESTURE_CONFIRM:
                                    try:
                                        if final_gesture == "FIST":
                                            mouse.left_click()
                                        elif final_gesture == "POINT":
                                            system.volume_up()
                                        elif final_gesture == "TWO":
                                            system.volume_down()
                                        elif final_gesture == "THREE":
                                            system.brightness_up()
                                        elif final_gesture == "FOUR":
                                            system.brightness_down()
                                        elif final_gesture == "SCROLL_UP":
                                            mouse.scroll_up()
                                        elif final_gesture == "SCROLL_DOWN":
                                            mouse.scroll_down()
                                    except:
                                        pass

                                    last_action_time = now

                    detector.draw_landmarks(frame, hand)

            if GLOBAL_STATE["voice_running"]:
                cv2.putText(frame, "VOICE ACTIVE",
                            (10, 160), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 220, 180), 2)

            ui.draw_frame(frame)

        except Exception as e:
            print("[MAIN] ERROR:", e)
            traceback.print_exc()
            continue

    if GLOBAL_STATE["voice_running"]:
        stop_voice_thread()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
