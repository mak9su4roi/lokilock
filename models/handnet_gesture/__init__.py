from enum import IntEnum, auto
from typing import Callable

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.python.solutions.hands import HandLandmark

Hand = dict[HandLandmark, dict]


class Gesture(IntEnum):
    SQUEEZED = auto()
    OPEN = auto()
    NONE = auto()


def load() -> Callable[[np.ndarray], tuple[Gesture, tuple[int, int, int, int]]]:
    model = mp.solutions.hands.Hands(
        model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5
    )

    def to_lm(hand, h, w) -> tuple[Hand, tuple[float, float, float, float]]:
        landmarks = hand.landmark
        landmarks = {
            e: (w * hand.landmark[e.value].x, h * hand.landmark[e.value].y)
            for e in HandLandmark
        }
        min_x, min_y, max_x, max_y = map(
            int,
            (
                min(landmarks.values(), key=lambda x_y: x_y[0])[0],
                min(landmarks.values(), key=lambda x_y: x_y[1])[1],
                max(landmarks.values(), key=lambda x_y: x_y[0])[0],
                max(landmarks.values(), key=lambda x_y: x_y[1])[1],
            ),
        )
        return landmarks, [min_x, min_y, max_x, max_y]

    def detect(frame) -> Gesture:
        h, w, _ = frame.shape
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if not (res := model.process(image).multi_hand_landmarks):
            return Gesture.NONE
        hand, _ = to_lm(res[0], h, w)

        i = (
            hand[HandLandmark.INDEX_FINGER_DIP][1]
            - hand[HandLandmark.INDEX_FINGER_MCP][1]
        )
        m = (
            hand[HandLandmark.MIDDLE_FINGER_DIP][1]
            - hand[HandLandmark.MIDDLE_FINGER_MCP][1]
        )
        r = (
            hand[HandLandmark.RING_FINGER_DIP][1]
            - hand[HandLandmark.RING_FINGER_MCP][1]
        )
        p = hand[HandLandmark.PINKY_DIP][1] - hand[HandLandmark.PINKY_MCP][1]
        if all(v > 0 for v in [m, r, p]):
            return Gesture.SQUEEZED
        if all(v < 0 for v in [i, m, r, p]):
            return Gesture.OPEN
        return Gesture.NONE

    return detect
