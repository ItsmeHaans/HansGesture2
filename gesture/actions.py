import math

class GestureActions:

    def detect_static(self, lm):

        fingers = []

        thumb_open = lm[4].x < lm[3].x
        fingers.append(thumb_open)

        tips = [8, 12, 16, 20]
        for t in tips:
            is_open = lm[t].y < lm[t - 2].y
            fingers.append(is_open)

        thumb, index, middle, ring, pinky = fingers

        # OPEN hand
        if all(fingers):
            return "OPEN"

        # FIST
        if not any(fingers):
            return "FIST"

        # ONE = point
        if index and not middle and not ring and not pinky:
            return "POINT"

        if thumb and not index and not middle and not ring and not pinky:
            return "THUMBS_UP"

        # TWO fingers
        if index and middle and not ring and not pinky:
            return "TWO"

        # THREE fingers
        if index and middle and ring and not pinky:
            return "THREE"

        # FOUR
        if index and middle and ring and pinky:
            return "FOUR"
        if pinky:
            return "PINCH"

        # FOUR
        if not index and middle and ring and pinky:
            return "GERMAN_3"

        # PINCH
        dist = math.dist(
            (lm[4].x, lm[4].y),
            (lm[8].x, lm[8].y)
        )
        if dist < 0.05:
            return "PINCH"

        return "UNKNOWN"
