import pathlib
import cv2
from ..utils import download_weights, cv2_to_mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


POINTS = pathlib.Path(__file__).parent / "points.tflite"
POINTS_URL = "https://www.dropbox.com/s/pzzwxftf6e4hxwr/points.tflite?dl=1"


def crop(
    image,
    bbox,
    size=(128, 128),
):
    x, y, e = bbox
    return cv2.resize(image[y : y + e, x : x + e], size, cv2.IMREAD_UNCHANGED)


def bounding_box(bb):
    x, y, _, e = bb.origin_x, bb.origin_y, bb.height, bb.width
    y = max(0, y - int(0.4 * e))
    x = max(0, x - int(0.2 * e))
    e += int(e * 0.4)
    return x, y, e


def load(points: pathlib.Path = POINTS):
    download_weights(POINTS, POINTS_URL)
    base_options = python.BaseOptions(model_asset_path=points)
    options = vision.FaceDetectorOptions(
        base_options=base_options, min_detection_confidence=0.6
    )
    detector = vision.FaceDetector.create_from_options(options)
    return lambda image: [
        (bounding_box(detection.bounding_box), detection.categories[0].score)
        for detection in detector.detect(cv2_to_mp(image)).detections
    ]
