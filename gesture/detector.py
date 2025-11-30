import mediapipe as mp
import math

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.mp_draw = mp.solutions.drawing_utils

    def process(self, frame_rgb):
        return self.hands.process(frame_rgb)

    def draw_landmarks(self, frame, hand_landmarks):
        self.mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS
        )

    def get_handedness(self, results):
        if not results.multi_handedness:
            return None
        label = results.multi_handedness[0].classification[0].label
        return label    # "Left" or "Right"

    def _dist(self, a, b):
        return math.dist((a.x, a.y), (b.x, b.y))

    def get_finger_states(self, lm, handside="Right"):
        """
        Return array [thumb, index, middle, ring, pinky]
        1=open, 0=closed
        """

        fingers = []

        # --- Thumb ---
        if handside == "Right":
            thumb_open = lm[4].x < lm[3].x
        else:  # Left hand mirror
            thumb_open = lm[4].x > lm[3].x

        fingers.append(1 if thumb_open else 0)

        # Index–pinky TIP-MCP > PIP-MCP
        tip_ids = [8, 12, 16, 20]
        pip_ids = [6, 10, 14, 18]
        mcp_ids = [5, 9, 13, 17]

        for tip, pip, mcp in zip(tip_ids, pip_ids, mcp_ids):
            dist_tip = self._dist(lm[tip], lm[mcp])
            dist_pip = self._dist(lm[pip], lm[mcp])
            fingers.append(1 if dist_tip > dist_pip else 0)

        return fingers
