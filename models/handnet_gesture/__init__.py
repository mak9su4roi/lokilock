import pathlib

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from ..utils import cv2_to_mp, download_weights

POINTS = pathlib.Path(__file__).parent / "points.task"
POINTS_URL = "https://www.dropbox.com/s/2q8bd6mi1p2bt24/points.task?dl=1"


def bounding_box(h, w, landmarks):
    hand = {id: (int(lm.x * w), int(lm.y * h)) for id, lm in enumerate(landmarks)}
    x0 = min(hand.values(), key=lambda c: c[0])[0]
    x1 = max(hand.values(), key=lambda c: c[0])[0]
    y0 = min(hand.values(), key=lambda c: c[1])[1]
    y1 = max(hand.values(), key=lambda c: c[1])[1]
    return x0, y0, abs(x1 - x0), abs(y1 - y0)


def closest_hand(h, w, recognition):
    hands = [
        {
            "bbox": bounding_box(h, w, landmarks),
            "handedness": handedness[0].category_name,
            "gesture": gestures[0].category_name,
        }
        for gestures, handedness, landmarks in zip(
            recognition.gestures, recognition.handedness, recognition.hand_landmarks
        )
    ]
    return max(hands, key=lambda g: g["bbox"][2] * g["bbox"][3]) if hands else None


def load():
    download_weights(POINTS, POINTS_URL)
    base_options = python.BaseOptions(model_asset_path=POINTS)
    options = vision.GestureRecognizerOptions(base_options=base_options)
    recognizer = vision.GestureRecognizer.create_from_options(options)
    return lambda image: recognizer.recognize(cv2_to_mp(image))
