# voice_runner.py
from services.voice_manager import VoiceManager
import time

API_KEY = "AIzaSyAlqOmzYxF1MD5gfACpByyUZSJX5JfJWQo"

# INSTANCE GLOBAL
vm = None
running = False


def run_voice_assistant():
    global vm, running

    if running:
        print("[VoiceRunner] Already running.")
        return

    vm = VoiceManager(API_KEY)
    vm.start_listening()

    running = True
    print("[VoiceRunner] Voice assistant started.")

    try:
        while running:
            time.sleep(0.1)
    except:
        pass

    print("[VoiceRunner] Loop ended.")


def stop_voice_assistant():
    global vm, running

    if not running or vm is None:
        print("[VoiceRunner] Not running.")
        return

    try:
        vm.stop_listening()
        print("[VoiceRunner] Voice assistant stopped.")
    except Exception as e:
        print("[VoiceRunner] Stop error:", e)

    running = False
    vm = None
