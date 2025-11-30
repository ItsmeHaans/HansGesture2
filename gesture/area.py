# gesture/area.py

class LeftAreaSelector:
    def detect(self, lm, gesture):
        """
        lm = landmarks
        gesture = string dari actions.detect_static()
        """

        # 1. Fist only
        if gesture != "FIST":
            return None

        x = lm[0].x   # wrist
        y = lm[0].y   # vertical position 0–1

        # 2. Must be inside left 20%
        if x > 0.20:
            return None


