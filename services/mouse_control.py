import pyautogui


class MouseControl:
    def __init__(self):
        pyautogui.FAILSAFE = False
        # Mengubah: Menyimpan posisi tangan/landmark sebelumnya (normalized coordinates 0.0 - 1.0)
        # untuk menghitung seberapa jauh tangan bergerak dari frame sebelumnya.
        self.prev_norm_x = None
        self.prev_norm_y = None

        # Mengubah: 'smooth' diganti menjadi 'sensitivity' (kecepatan kursor).
        # Nilai yang lebih besar akan menghasilkan pergerakan kursor yang lebih cepat
        # untuk gerakan tangan yang sama.
        self.sensitivity = 3  # Anda bisa menyesuaikan angka ini (misalnya 20, 40, dst.)

    def move_cursor(self, lm):
        # 1. Ambil posisi tangan saat ini (normalized coordinates)
        current_norm_x = lm[0].x
        current_norm_y = lm[0].y

        # Inisialisasi posisi awal (hanya terjadi pada frame pertama)
        if self.prev_norm_x is None:
            self.prev_norm_x = current_norm_x
            self.prev_norm_y = current_norm_y
            return  # Keluar pada frame pertama agar tidak ada pergerakan yang tiba-tiba

        # 2. Hitung perbedaan (delta) posisi tangan dari frame sebelumnya
        dx_norm = current_norm_x - self.prev_norm_x
        dy_norm = current_norm_y - self.prev_norm_y

        # 3. Konversi delta normalized menjadi delta pixel layar
        # Kita perlu mengalikan delta normalized dengan faktor pengali besar (sensitivity)
        # dan juga ukuran layar (screen_w) agar pergerakan terasa signifikan.
        screen_w, _ = pyautogui.size()

        # Faktor pengali tambahan (misalnya 1.5) dapat digunakan untuk tuning akhir.
        dx_pixel = dx_norm * self.sensitivity * screen_w * 1.8
        dy_pixel = dy_norm * self.sensitivity * screen_w * 1.8

        # 4. Pindahkan kursor secara RELATIF
        # pyautogui.move() memindahkan kursor sejauh (dx_pixel, dy_pixel) dari posisi saat ini.
        pyautogui.move(dx_pixel, dy_pixel)

        # 5. Simpan posisi tangan saat ini sebagai posisi 'sebelumnya' untuk frame berikutnya
        self.prev_norm_x = current_norm_x
        self.prev_norm_y = current_norm_y

    def left_click(self):
        pyautogui.click()

    def scroll_up(self):
        pyautogui.scroll(600)

    def scroll_down(self):
        pyautogui.scroll(-600)