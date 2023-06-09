import cv2
import mediapipe as mp


def crop(
    image,
    bbox,
    size=(128, 128),
):
    x, y, e = bbox
    return cv2.resize(image[y : y + e, x : x + e], size, cv2.IMREAD_UNCHANGED)


def bounding_box(bb, h, w, *_):
    x, y, e = map(lambda a: getattr(bb, a), ["xmin", "ymin", "width"])
    y = max(0, y - 0.4 * e)
    x = max(0, x - 0.2 * e)
    e += e * 0.4
    return *map(int, [x*w, y*h, e*w]),


def load():
    model = mp.solutions.face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5
    )
    def detect(image):
        return [ 
            (bounding_box(res.location_data.relative_bounding_box, *image.shape), res.score)
            for res in (model.process(image).detections or [])
        ]
    return detect
