# gesture/position.py
import math

class AdvancedGesture:
    def __init__(self):
        self.prev_y_1 = None
        self.prev_y_2 = None
        self.prev_y_3 = None
        self.scroll_prev_y = None

    # 1 finger swipe up
    def one_finger_up(self, lm):
        y = lm[8].y

        if self.prev_y_1 is None:
            self.prev_y_1 = y
            return None

        dy = self.prev_y_1 - y
        self.prev_y_1 = y

        if dy > 0.035:
            return "ONE_UP"

        return None

    # 2 finger swipe up (volume down)
    def two_finger_up(self, lm):
        avg = (lm[8].y + lm[12].y) / 2

        if self.prev_y_2 is None:
            self.prev_y_2 = avg
            return None

        dy = self.prev_y_2 - avg
        self.prev_y_2 = avg

        if dy > 0.035:
            return "TWO_UP"

        return None

    # 3 finger swipe up (brightness down)
    def three_finger_up(self, lm):
        avg = (lm[8].y + lm[12].y + lm[16].y) / 3

        if self.prev_y_3 is None:
            self.prev_y_3 = avg
            return None

        dy = self.prev_y_3 - avg
        self.prev_y_3 = avg

        if dy > 0.045:
            return "THREE_UP"

        return None

    # german three (middle + ring + pinky)
    def german_three(self, fingers):
        thumb, index, middle, ring, pinky = fingers

        if (middle == 1 and ring == 1 and pinky == 1 and thumb == 0 and index == 0):
            return "GERMAN_3"
        return None

    # Scroll gesture: "7" = thumb + index only
    def scroll(self, fingers, lm):
        thumb, index, middle, ring, pinky = fingers

        # Gesture = 7 (scroll mode)
        gesture_7 =  thumb and index

        if gesture_7:

            # gunakan index finger (lebih sensitif) dibanding wrist
            y = lm[8].y

            # init frame pertama
            if self.scroll_prev_y is None:
                self.scroll_prev_y = y
                return None

            dy = self.scroll_prev_y - y
            self.scroll_prev_y = y

            # threshold lebih kecil (0.01 – 0.015)
            if dy > 0.015:
                return "SCROLL_UP"
            elif dy < -0.015:
                return "SCROLL_DOWN"

        else:
            # gesture berubah → reset posisi awal
            self.scroll_prev_y = None

        return None


