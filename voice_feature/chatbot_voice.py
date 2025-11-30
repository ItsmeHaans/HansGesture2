# voice_chatbot.py
import speech_recognition as sr
import pygame
import threading
import time
import subprocess
import sys
import shlex
import os

from .ai_manager2 import AIManager2


class VoiceChatBot:
    def __init__(self, api_key):

        # STT
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 100
        self.recognizer.dynamic_energy_threshold = True

        # sounds
        pygame.mixer.init()
        self.notif = "voice_feature/notif/notif.mp3"

        # AI
        self.ai = AIManager2(api_key)

        # state
        self.active = False
        self.silence_timeout = 5  # seconds

    # -----------------------------------------
    # TTS via subprocess (work 100%)
    # -----------------------------------------
    def safe_tts(self, text):
        worker = os.path.join(os.path.dirname(__file__), "tts_worker.py")
        cmd = f"{sys.executable} {worker} {shlex.quote(text)}"
        subprocess.Popen(cmd, shell=True)

    # -----------------------------------------
    def play_and_wait(self, path):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    # -----------------------------------------
    def start_chat(self, callback=None):
        if self.active:
            return

        self.active = True
        threading.Thread(
            target=self._loop, args=(callback,), daemon=True
        ).start()

    # -----------------------------------------
    def _loop(self, callback):
        self.play_and_wait(self.notif)
        time.sleep(0.4)

        print("[Chatbot] Listening...")
        last_talk = time.time()
        waiting_ai = False

        with sr.Microphone() as mic:
            self.recognizer.adjust_for_ambient_noise(mic, duration=0.6)

            while self.active:

                # silence check
                if not waiting_ai and time.time() - last_talk > self.silence_timeout:
                    self.play_and_wait(self.notif)
                    self.safe_tts("Chat ended")
                    print("[Chatbot] Session ended")
                    self.active = False
                    return

                # listen
                try:
                    audio = self.recognizer.listen(mic, timeout=4, phrase_time_limit=7)
                except sr.WaitTimeoutError:
                    continue

                # STT
                try:
                    user = self.recognizer.recognize_google(audio)
                except:
                    continue

                print("[User]", user)
                last_talk = time.time()
                waiting_ai = True

                # -------------------------
                # AI CALLBACK
                # -------------------------
                def ai_response(aitype, reply):
                    nonlocal waiting_ai, last_talk

                    print("[AI]", reply)

                    if callback:
                        callback(user, reply)

                    self.safe_tts(reply)

                    waiting_ai = False
                    last_talk = time.time()

                # call AI (async)
                self.ai.ask(user, ai_response)
