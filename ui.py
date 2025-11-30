import pygame
import cv2
import numpy as np


class GestureUI:
    def __init__(self):
        pygame.init()

        WINDOW_WIDTH = 1920
        WINDOW_HEIGHT = 980

        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hand Gesture AI")

        # Background kamu
        self.background = pygame.image.load("background.png")

        self.video_x = 240
        self.video_y = 192

        # Ukuran video yang Anda tetapkan
        self.video_w = 1280
        self.video_h = 720
        self.radius = 8  # Radius kelengkungan sudut

        # BARU: Buat Masker (Surface) dengan Sudut Melengkung
        self.rounded_mask = self._create_rounded_mask()

    def _create_rounded_mask(self):
        """Membuat surface hitam dengan area melengkung transparan (alpha channel)."""
        # Surface dengan alpha channel
        mask_surface = pygame.Surface((self.video_w, self.video_h), pygame.SRCALPHA)
        mask_surface.fill((255, 255, 255, 0))  # Isi dengan transparan (putih, alpha 0)

        # Gambar persegi panjang putih (penuh alpha 255) yang melengkung di atas surface transparan
        # Warna (255, 255, 255) dan alpha 255 akan menjadi area yang DITAMPILKAN
        pygame.draw.rect(mask_surface, (255, 255, 255, 255),
                         (0, 0, self.video_w, self.video_h),
                         border_radius=self.radius)

        return mask_surface

    def draw_frame(self, frame):
        # 1. Resize dan Flip Frame CV2
        frame = cv2.resize(frame, (self.video_w, self.video_h))

        # PERBAIKAN 1: Membalik frame secara horizontal (Mirror Image Fix)
        frame = cv2.flip(frame, 1)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 2. Konversi ke Pygame Surface
        # Rotasi tetap diperlukan jika orientasi CV2 dan Pygame berbeda
        frame_surface = pygame.surfarray.make_surface(np.rot90(frame))

        # 3. Draw Background
        self.window.blit(self.background, (0, 0))

        # 4. TERBARU: Buat Surface Target untuk Masking
        # Surface ini akan menampung frame video yang sudah dipotong.
        target_surface = pygame.Surface((self.video_w, self.video_h), pygame.SRCALPHA)
        target_surface.fill((0, 0, 0, 0))  # Isi dengan transparan

        # 5. Aplikasikan Masker ke Surface Video
        # Surface video di-blit ke surface target
        target_surface.blit(frame_surface, (0, 0))

        # Set alpha mask: hanya area putih dari self.rounded_mask yang akan ditampilkan
        # Ini akan memotong sudutnya
        target_surface.blit(self.rounded_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # 6. Gambar Frame (yang sudah melengkung) ke Window Utama
        self.window.blit(target_surface, (self.video_x, self.video_y))

        pygame.display.update()

    def check_quit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
        return False