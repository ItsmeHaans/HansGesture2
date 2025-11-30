from timer_voice import VoiceTimer

def timer_callback(seconds, spoken_text):
    print("=== CALLBACK RECEIVED ===")
    print("Spoken text :", spoken_text)
    print("Timer value :", seconds)

if __name__ == "__main__":
    print("=== TEST VOICE TIMER ===")
    print("Ketika notif.mp3 berbunyi, ucapkan angka (contoh: 'ten', '5', 'two').")
    print("Timer akan mulai jika berhasil.")

    timer = VoiceTimer()
    timer.start_timer_voice(callback=timer_callback)

    # keep program alive
    import time
    while True:
        time.sleep(1)
