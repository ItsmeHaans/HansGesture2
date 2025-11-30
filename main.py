import cv2
import time
import threading
import traceback

# ui removed (headless)
# from ui import GestureUI
from gesture.detector import GestureDetector
from gesture.actions import GestureActions
from gesture.position import AdvancedGesture
from gesture.area import LeftAreaSelector

from services.app_launcher import AppLauncher
from services.mouse_control import MouseControl
from services.system_control import SystemControl

# VOICE RUNNER
from services.voice_runner import run_voice_assistant, stop_voice_assistant

# -----------------------
# Shared frame buffer (for MJPEG streaming)
# -----------------------
import threading as _th

LATEST_FRAME_LOCK = _th.Lock()
LATEST_FRAME_JPEG = None  # bytes of last encoded JPEG


def set_latest_frame_jpeg(jpeg_bytes):
    global LATEST_FRAME_JPEG
    with LATEST_FRAME_LOCK:
        LATEST_FRAME_JPEG = jpeg_bytes


def get_latest_frame_jpeg():
    with LATEST_FRAME_LOCK:
        return LATEST_FRAME_JPEG


# =====================================================
# VOICE THREAD CONTROLLER
# =====================================================
def start_voice_thread(state):
    if state["voice_running"]:
        return False

    def _runner():
        try:
            run_voice_assistant()
        except Exception as e:
            print("[VoiceThread] ERROR")
            traceback.print_exc()
        finally:
            state["voice_running"] = False
            state["voice_thread"] = None
            print("[VoiceThread] EXITED")

    t = threading.Thread(target=_runner, daemon=True)
    state["voice_thread"] = t
    state["voice_running"] = True
    t.start()
    print("[VoiceThread] STARTED")
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
        t.join(timeout=1.0)

    state["voice_running"] = False
    state["voice_thread"] = None
    print("[VoiceThread] STOPPED")
    return True


# =====================================================
# MAIN APPLICATION (headless)
# =====================================================
def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1920)
    cap.set(4, 720)

    # ui removed (headless)
    detector = GestureDetector()
    static = GestureActions()
    motion = AdvancedGesture()
    area = LeftAreaSelector()

    launcher = AppLauncher()
    mouse = MouseControl()
    system = SystemControl()

    # =====================================================
    # STATUS FLAGS
    # =====================================================
    freehand_enabled = False
    open_start_time = None
    OPEN_HOLD_TIME = 3

    gesture_start = None
    last_gesture = None
    GESTURE_CONFIRM = 0.5
    COOLDOWN = 0.5
    last_action_time = 0

    # =====================================================
    # VOICE STATE
    # =====================================================
    state = {
        "voice_running": False,
        "voice_thread": None
    }

    german_hold_start = None
    GERMAN_HOLD = 1.0   # 1 detik

    try:
        print("[MAIN] Starting headless gesture loop (Ctrl+C to exit)")
        while True:
            try:
                # no ui.check_quit() — run until interrupted
                ret, frame = cap.read()
                if not ret or frame is None:
                    print("[MAIN] no frame from camera, sleeping briefly")
                    time.sleep(0.1)
                    continue

                frame = cv2.flip(frame, 1)
                # keep similar resize so drawing coordinates remain correct
                frame = cv2.resize(frame, (1456, 783))

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = detector.process(rgb)

                if results and results.multi_hand_landmarks:
                    for hand in results.multi_hand_landmarks:

                        lm = hand.landmark
                        fingers = detector.get_finger_states(lm)
                        static_gesture = static.detect_static(lm)

                        # FREE-HAND OFF → using PINCH (NEW)
                        if static_gesture == "PINCH":
                            freehand_enabled = False
                            open_start_time = None

                        # AREA SELECTION (LEFT)
                        zone = area.detect(lm, static_gesture)
                        if zone:
                            try:
                                launcher.run(zone)
                            except:
                                pass

                            detector.draw_landmarks(frame, hand)
                            cv2.putText(frame, zone, (10, 40),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                                        (0, 255, 255), 2)
                            continue

                        # MOTION GESTURES
                        one = motion.one_finger_up(lm)
                        two = motion.two_finger_up(lm)
                        three = motion.three_finger_up(lm)
                        scroll = motion.scroll(fingers, lm)
                        german = motion.german_three(fingers)

                        if scroll:
                            final_gesture = scroll
                        else:
                            # default behavior
                            final_gesture = static_gesture
                            for g in [one, two, three, german]:
                                if g:
                                    final_gesture = g

                        # START VOICE (GERMAN 3 HOLD 1s)
                        if final_gesture == "GERMAN_3":
                            if not state["voice_running"]:
                                if german_hold_start is None:
                                    german_hold_start = time.time()

                                elapsed = time.time() - german_hold_start
                                cv2.putText(frame, f"VOICE IN {max(0, GERMAN_HOLD-elapsed):.1f}",
                                            (10, 120), cv2.FONT_HERSHEY_SIMPLEX,
                                            0.7, (0, 200, 255), 2)

                                if elapsed >= GERMAN_HOLD:
                                    print("[Gesture] GERMAN_3 → Start Voice")
                                    start_voice_thread(state)
                                    german_hold_start = None
                            else:
                                german_hold_start = None

                            detector.draw_landmarks(frame, hand)
                            # previously ui.draw_frame(frame) — now set latest frame for streamer
                            _, jpeg = cv2.imencode('.jpg', frame)
                            set_latest_frame_jpeg(jpeg.tobytes())
                            continue

                        else:
                            german_hold_start = None

                        # STOP VOICE (THUMB_UP)
                        if final_gesture == "THUMBS_UP":
                            if state["voice_running"]:
                                print("[Gesture] THUMBS_UP → Stop Voice")
                                stop_voice_thread(state)

                            detector.draw_landmarks(frame, hand)
                            cv2.putText(frame, "THUMBS_UP", (10, 40),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                                        (0, 120, 255), 2)
                            # set latest frame for streamer
                            _, jpeg = cv2.imencode('.jpg', frame)
                            set_latest_frame_jpeg(jpeg.tobytes())
                            continue

                        # FREE-HAND (OPEN HOLD)
                        if static_gesture == "OPEN":

                            if not freehand_enabled:

                                if open_start_time is None:
                                    open_start_time = time.time()

                                elapsed = time.time() - open_start_time

                                if elapsed < OPEN_HOLD_TIME:
                                    rem = OPEN_HOLD_TIME - elapsed
                                    cv2.putText(frame, f"HOLD OPEN: {rem:.1f}s",
                                                (10, 80),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                                (0, 200, 255), 2)

                                if elapsed >= OPEN_HOLD_TIME:
                                    freehand_enabled = True

                            if freehand_enabled:
                                mouse.move_cursor(lm)

                        else:
                            if not freehand_enabled:
                                open_start_time = None

                        # GESTURE ACTIONS
                        actionable = ["FIST", "POINT", "TWO",
                                      "THREE", "FOUR",
                                      "SCROLL_UP", "SCROLL_DOWN"]

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
                        cv2.putText(frame, final_gesture, (10, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    (0, 255, 0), 2)

                # DISPLAY VOICE ACTIVE STATUS
                if state["voice_running"]:
                    cv2.putText(frame, "VOICE ACTIVE",
                                (10, 160), cv2.FONT_HERSHEY_SIMPLEX,
                                0.8, (0, 220, 180), 2)

                # instead of ui.draw_frame(frame), encode and set latest frame for streaming
                _, jpeg = cv2.imencode('.jpg', frame)
                set_latest_frame_jpeg(jpeg.tobytes())

            except Exception as e:
                print("[MAIN] ERROR:", e)
                traceback.print_exc()
                # continue main loop
                continue

    except KeyboardInterrupt:
        print("[MAIN] KeyboardInterrupt received, exiting main loop")

    finally:
        # CLEANUP
        if state["voice_running"]:
            stop_voice_thread(state)

        try:
            cap.release()
        except:
            pass

        print("[MAIN] Exited cleanly")


if __name__ == "__main__":
    main()
