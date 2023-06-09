import picamera2
import numpy as np
import cv2
from common.types.event import Event

from .. import task as _task
from ..constants import EventType


@_task.shedule_producer
def task(tx: _task.Transmitter):
    camera = picamera2.Picamera2()
    camera.configure(
        camera.create_preview_configuration(
            {
           "format": 'RGB888',
            "size": (1024, 1024),
            }
        )
    )
    camera.options["quality"] = 10
    camera.start()
    try:
        while True:
            frame = np.rot90(camera.capture_array())
            tx(Event(type=EventType.CAMERA_FRAME, data=frame))
            cv2.imwrite("/log/stream.png", frame)
    finally:
        camera.close()

