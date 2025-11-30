# backend_voice_timer.py
from .timer_voice import VoiceTimer

def run_voice_timer():
    """
    Dipanggil dari frontend, mengembalikan:
    {
        "seconds": 0,
        "spoken_text": "ten"
    }
    """
    result = {"seconds": 0, "spoken_text": ""}

    def timer_callback(seconds, spoken_text):
        result["seconds"] = seconds
        result["spoken_text"] = spoken_text

    timer = VoiceTimer()
    timer.start_timer_voice(callback=timer_callback)

    return result
