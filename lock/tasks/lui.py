import cv2
import numpy as np

from common.types.event import Event

from ..settings import settings
from . import task as _task
from .constants import EventType
from .helpers import event_stream


def update_text(
    canvas: np.ndarray,
    text: str,
    loc: tuple,
    width=None,
    bcolor: tuple = (255, 255, 255),
    fcolor: tuple = (0, 0, 0),
):
    x0, y0, h = np.array([4, 4, 0]) + loc
    x1, y1 = (canvas.shape[1] - 4) if width is None else x0 + width, y0 + h
    canvas[y0:y1, x0:x1] = bcolor
    cv2.rectangle(canvas, (x0, y0), (x1, y1), color=(0, 255, 0), thickness=2)
    cv2.putText(
        canvas,
        text,
        (x0 + 14, y0 + 30),
        cv2.FONT_HERSHEY_PLAIN,
        1,
        fcolor,
        1,
        cv2.LINE_AA,
        False,
    )


@_task.shedule_consumer
def task(rx: _task.Receiver):
    face = None
    ready = None
    user = None
    evt: Event
    canvas, canvas_shape = None, None

    lock_info = (148, 0, 46)
    lock_status = (148, 46, 46)
    door_status = (148, 92, 46)

    lable = np.array([180, 0, 0])

    def allocate_canvas(shape, fill=255):
        canvas = np.zeros(shape, dtype=np.uint8)
        canvas.fill(fill)
        update_text(canvas, f"lock_id", lock_info, 180, bcolor=(200, 200, 200))
        update_text(canvas, settings.lock_id, lock_info + lable)

        update_text(canvas, f"door_status", door_status, 180, bcolor=(200, 200, 200))
        update_text(
            canvas,
            f"locked",
            door_status + lable,
            bcolor=(0, 0, 128),
            fcolor=(255, 255, 255),
        )

        update_text(canvas, f"lock_status", lock_status, 180, bcolor=(200, 200, 200))
        return canvas

    actions = []
    for evt in event_stream(rx):
        if evt.type is EventType.CAMERA_FRAME:
            frame = evt.data
            if canvas is None:
                canvas = allocate_canvas(np.array([148, 0, 0]) + frame.shape)
            canvas[148:] = frame
            [a() for a in actions]
            actions.clear()

            cv2.imshow("lokilock", canvas)
            cv2.waitKey(1)
        elif evt.type is EventType.ACTIVATION_FRAMES:
            user = "Detecting..."
            ready = False
            color = (0, 0, 0)
        elif evt.type is EventType.DETECTION_RSP:
            if evt.data is not None:
                canvas[10:138, 10:138] = evt.data
                actions += [
                    lambda: update_text(canvas, f"verifying", lock_status + lable)
                ]
        elif evt.type is EventType.ACTIVATION_RSP:
            actions += [
                lambda: update_text(
                    canvas, f"waiting for gesture", lock_status + lable
                ),
                lambda: update_text(
                    canvas,
                    f"locked",
                    door_status + lable,
                    bcolor=(0, 0, 128),
                    fcolor=(255, 255, 255),
                ),
            ]
        elif evt.type is EventType.VERIFICATION_RSP:
            result = evt.data
            actions += [
                lambda: update_text(canvas, f"idle", lock_status + lable),
                (
                    lambda: update_text(
                        canvas,
                        f"unlocked: {result}",
                        door_status + lable,
                        bcolor=(0, 128, 0),
                        fcolor=(255, 255, 255),
                    )
                )
                if isinstance(result, str)
                else (
                    lambda: update_text(
                        canvas,
                        f"locked: {result.value}",
                        door_status + lable,
                        bcolor=(0, 0, 128),
                        fcolor=(255, 255, 255),
                    )
                ),
            ]
