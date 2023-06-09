import cv2

from common.types.event import Event

from .. import task as _task
from ..constants import EventType


@_task.shedule_producer
def task(tx: _task.Transmitter):
    camera = cv2.VideoCapture(0)
    try:
        while True:
            _, frame = camera.read()
            if frame is not None:
                tx(Event(type=EventType.CAMERA_FRAME, data=frame))
    finally:
        camera.release()
