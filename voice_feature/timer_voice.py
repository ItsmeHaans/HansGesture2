import speech_recognition as sr
import pygame
import threading
import time
from services.tts_manager import TTSManager


class VoiceTimer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 100  # mic lebih sensitif
        self.recognizer.dynamic_energy_threshold = True

        self.tts = TTSManager()
        pygame.mixer.init()

        self.notif = "voice_feature/notif/notif.mp3"
        self.ring = "voice_feature/notif/ring.mp3"

    # ------------------------------------------------------
    def play_and_wait(self, path, volume=1.0):
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)  # ring lebih kencang
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    # ------------------------------------------------------
    def listen_for_number(self):
        print("[STT] Listening... (waiting up to 10 seconds)")

        with sr.Microphone() as mic:
            # mic lebih sensitif + lebih lama adaptasi
            self.recognizer.adjust_for_ambient_noise(mic, duration=0.8)

            try:
                audio = self.recognizer.listen(
                    mic,
                    timeout=10,            # lebih panjang
                    phrase_time_limit=8    # bicara lebih lama
                )
            except sr.WaitTimeoutError:
                print("[STT] Timeout — no speech detected")
                return None, None

        try:
            text = self.recognizer.recognize_google(audio).lower()
            print("[User said]", text)

            minutes = self.parse_to_minutes(text)
            return minutes, text

        except Exception as e:
            print("[STT] Error:", e)
            return None, None

    # ------------------------------------------------------
    def parse_to_minutes(self, text):
        # mapping angka bahasa Inggris → menit
        words = {
            "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8,
            "nine": 9, "ten": 10
        }

        for w, n in words.items():
            if w in text:
                return n

        # angka langsung
        for part in text.split():
            if part.isdigit():
                return int(part)

        return None

    # ------------------------------------------------------
    def start_timer_voice(self, callback=None):
        threading.Thread(target=self._run, args=(callback,), daemon=True).start()

    def _run(self, callback):
        print("[Timer] Playing notif...")
        self.play_and_wait(self.notif)

        time.sleep(1)   # delay sebelum mic dibuka → biar user siap

        minutes, spoken = self.listen_for_number()

        if minutes is None:
            self.tts.say("I did not hear any number")
            return

        if callback:
            callback(minutes, spoken)

        self.tts.say(f"Timer set for {minutes} minutes.")

        total_seconds = minutes * 60
        for remaining in range(total_seconds, 0, -1):
            print("TIMER:", remaining, "seconds")
            time.sleep(1)

        self.play_and_wait(self.ring, volume=1.3)
        self.tts.say("Timer finished.")
