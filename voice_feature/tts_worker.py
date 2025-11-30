# tts_worker.py (Solusi menggunakan gTTS)
import sys
import pygame
import time
from gtts import gTTS  # <-- Tambahkan import ini


# import google.generativeai as genai # <-- Hapus atau biarkan tidak terpakai

# API_KEY = "AIzaSyAlqOmzYxF1MD5gfACpByyUZSJX5JfJWQo" # <-- Tidak perlu API key di sini

def speak(text):
    path = "tts_output.mp3"
    try:
        # 1. Buat audio menggunakan gTTS
        tts = gTTS(text=text, lang='en')  # Ganti 'en' ke 'id' jika perlu bahasa Indonesia
        tts.save(path)

        # 2. Play audio
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

        # Tambahkan delay untuk memastikan audio dimuat
        time.sleep(0.1)

        # Tunggu sampai selesai
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)

        # Opsional: Hapus file setelah selesai
        # os.remove(path)

    except Exception as e:
        print("[TTS Worker Error]", e)


if __name__ == "__main__":
    # ... (sisanya sama)
    if len(sys.argv) < 2:
        sys.exit(0)

    # Pastikan teks yang diparsing dari sys.argv[1] sudah benar
    text = sys.argv[1]
    speak(text)