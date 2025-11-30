import speech_recognition as sr
from smart_launcher import SmartLauncher

class SpeechControl:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.launcher = SmartLauncher()

    def listen(self):
        with sr.Microphone() as mic:
            self.recognizer.adjust_for_ambient_noise(mic)

            while True:
                try:
                    audio = self.recognizer.listen(mic)
                    command = self.recognizer.recognize_google(audio).lower()
                    print("[You]:", command)
                    self.handle(command)
                except:
                    pass

    def handle(self, command):
        trigger_words = ["open", "buka", "jalankan", "run", "launch", "start"]

        for t in trigger_words:
            if command.startswith(t):
                app = command.replace(t, "").strip()
                self.launcher.open(app)
                return
