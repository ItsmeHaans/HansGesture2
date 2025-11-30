import speech_recognition as sr
import threading
import webbrowser
import pygame

from services.tts_manager import TTSManager
from services.app_launcher import AppLauncher
from services.ai_manager import AIManager


class VoiceManager:
    def __init__(self, api_key):

        self.recognizer = sr.Recognizer()
        self.tts = TTSManager()
        self.launcher = AppLauncher()
        self.ai = AIManager(api_key)

        self.is_listening = False
        self._listening_thread = None

        pygame.mixer.init()
        self.sound_notif = "notif.mp3"

    # =====================================================
    def play_sound(self, path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print("[Sound Error]", e)

    # =====================================================
    def start_listening(self):
        if self.is_listening:
            return

        self.is_listening = True

        # Simpan thread agar dapat dihentikan bersih
        self._listening_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self._listening_thread.start()

        print("[Voice] Listening...")

    # =====================================================
    def stop_listening(self):
        # Matikan flag
        self.is_listening = False

        # Stop pygame audio
        try:
            pygame.mixer.music.stop()
        except:
            pass

        # Tunggu thread selesai
        if self._listening_thread and self._listening_thread.is_alive():
            self._listening_thread.join(timeout=1)

        print("[Voice] Listening stopped.")

    # =====================================================
    def _listen_loop(self):
        with sr.Microphone() as mic:

            try:
                self.recognizer.adjust_for_ambient_noise(mic, duration=1)
            except:
                pass

            while self.is_listening:
                try:
                    audio = self.recognizer.listen(
                        mic, timeout=4, phrase_time_limit=5
                    )

                    if not self.is_listening:
                        break

                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                    except:
                        continue

                    print("[User]", text)
                    self.handle_command(text)

                except:
                    pass

    # =====================================================
    # COMMAND PROCESSOR
    # =====================================================
    def handle_command(self, text):

        text = text.lower().strip()

        # =================================================
        # 1) OPEN X ON MY DESKTOP
        # =================================================
        if "on my desktop" in text:
            app = text.replace("on my desktop", "").replace("open", "").replace("buka", "").strip()
            ok = self.launcher.open_app(app)
            if ok:
                self.tts.say(f"Opening {app}")
            else:
                self.tts.say(f"I cannot find {app} on your desktop")
            return

        # =================================================
        # 2) OPEN X (local first)
        # =================================================
        if text.startswith("open") or text.startswith("buka"):
            app = text.replace("open", "").replace("buka", "").strip()
            print("[System] Local open request:", app)

            ok = self.launcher.open_app(app)
            if ok:
                self.tts.say(f"Opening {app}")
                return
            else:
                print("[System] Not found locally → fallback to AI")

        # =================================================
        # 3) FALLBACK TO AI
        # =================================================
        def ai_callback(result_type, result_value):

            # ---- AI says it's a local app
            if result_type == "local_app":
                app = result_value.replace("open", "").replace("buka", "").strip()
                ok = self.launcher.open_app(app)
                if ok:
                    self.tts.say(f"Opening {app}")
                else:
                    self.tts.say(f"I cannot find {app}")
                return

            # ---- AI returned link
            if result_type == "link":
                self.tts.say("Opening link")
                webbrowser.open(result_value)
                return

            # ---- Chatbot
            cleaned = result_value.replace("\n", " ")
            self.tts.say(cleaned)

        # SEND TO AI
        self.ai.ask(text, ai_callback)
