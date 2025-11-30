import pyttsx3
import threading


class TTSManager:
    def __init__(self):
        self.engine = pyttsx3.init()

        # ==========================
        # Voice Configuration
        # ==========================
        voices = self.engine.getProperty('voices')

        # Try to choose an English male voice (more AI-like)
        selected_voice = None
        for v in voices:
            if "male" in v.name.lower() or "david" in v.name.lower():
                selected_voice = v.id
                break

        # If no male found, fallback
        if selected_voice is None:
            selected_voice = voices[0].id

        self.engine.setProperty('voice', selected_voice)
        self.engine.setProperty('rate', 165)   # Speaking speed
        self.engine.setProperty('volume', 1.0) # Max volume

    # ==========================
    # INTERNAL SPEAK (BLOCKING)
    # ==========================
    def _speak(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"[TTS Error] {e}")

    # ==========================
    # PUBLIC SPEAK (NON-BLOCKING)
    # ==========================
    def say(self, text):
        thread = threading.Thread(target=self._speak, args=(text,), daemon=True)
        thread.start()
