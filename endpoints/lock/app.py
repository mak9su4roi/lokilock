import os
import queue
import random
import threading
import time
from enum import Enum, auto

import cv2
import httpx

from api.verification import AuthReq, AuthRsp
from common.logging.logger import logger
from common.types.event import Event
from common.types.vector import Vector
from models import blazeface, edgenet_face, handnet_gesture
from port.stream import stream as video_stream


class EventType(Enum):
    CAMERA_FRAME = auto()
    RECOGNITION = auto()
    GESTURE = auto()
    RESET = auto()
    FACE = auto()


def auth_task(tx: queue.Queue):
    rx = queue.Queue()

    def task_():
        with httpx.Client(
            base_url=f"{os.environ['VERIFICATION_URL']}/auth/{os.environ['LOCK_ID']}"
        ) as verification:
            model = edgenet_face.load()
            for evt in iter(rx.get, None):
                face = evt.data
                try:
                    tx.put(
                        Event(
                            type=EventType.RECOGNITION,
                            data=AuthRsp(
                                **verification.post(
                                    url="/",
                                    data=AuthReq(
                                        data=Vector.from_tensor(model(face))
                                    ).json(),
                                ).json()
                            ).status,
                        )
                    )
                except Exception as error:
                    logger.error(str(error))
                    tx.put(Event(type=EventType.RECOGNITION, data=None))

    task = threading.Thread(target=task_, daemon=True)
    task.start()
    return lambda f: rx.put(f)


def face_task(tx: queue.Queue):
    rx = queue.Queue()

    def task_():
        def best_face(faces):
            return random.choice(faces)

        detector = blazeface.load()
        for frames in iter(rx.get, None):
            (
                faces := [
                    blazeface.crop(frame, res[0][0])
                    for frame in frames
                    if (res := detector(frame))
                ]
            ) and tx.put(Event(type=EventType.FACE, data=best_face(faces)))

    task = threading.Thread(target=task_, daemon=True)
    task.start()
    return lambda f: rx.put(f)


def gesture_task(tx: queue.Queue):
    rx = queue.Queue()

    class Gesture(Enum):
        OPEN_PALM = "Open_Palm"
        POINTING_UP = "Pointing_Up"
        NONE = "None"

    def task_():
        frames = []
        detector = handnet_gesture.load()
        reset_interval = 0.5

        for evt in filter(
            lambda e: e.type is EventType.CAMERA_FRAME
            and (time.time() - e.data.timestamp < 0.1),
            iter(rx.get, None),
        ):
            frame = evt.data
            h, w, _ = frame.data.shape
            result = handnet_gesture.closest_hand(h, w, detector(frame.data))
            if frames and frame.timestamp - frames[-1].timestamp > reset_interval:
                frames.clear()
            if not result or result["gesture"] == Gesture.NONE.value:
                continue
            gesture = result["gesture"]
            if gesture == Gesture.POINTING_UP.value:
                frames += [frame]
            elif gesture == Gesture.OPEN_PALM.value and len(frames) > 10:
                random.shuffle(frames)
                logger.info(f"Collected {len(frames)} frame(s)")
                capture = threading.Event()
                tx.put(
                    Event(
                        type=EventType.GESTURE,
                        data={
                            "frames": [frame.data for frame in frames[:10]],
                            "handle": capture,
                        },
                    )
                )
                frames.clear()
                capture.wait()
            else:
                frames.clear()

    task = threading.Thread(target=task_, daemon=True)
    task.start()
    return lambda f: rx.put(f)


def ui_task():
    rx = queue.Queue()

    def task_():
        face = None
        user = None
        ready = True
        color = (0, 0, 0)
        for evt in iter(rx.get, None):
            if evt.type is EventType.CAMERA_FRAME:
                canvas = evt.data.data
                canvas[0:138, 0:138] = 0
                canvas[138:178, 0:138] = 255
                canvas[:40, 138:] = 255
                if face is not None:
                    canvas[5 : face.shape[0] + 5, 5 : face.shape[1] + 5] = face
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 1
                thickness = 1
                user and cv2.putText(
                    canvas,
                    user,
                    (140, 28),
                    font,
                    fontScale,
                    color,
                    thickness,
                    cv2.LINE_AA,
                    False,
                )
                cv2.putText(
                    canvas,
                    "READY" if ready else "IDLE",
                    (0, 168),
                    font,
                    fontScale,
                    (0, 100, 0),
                    thickness,
                    cv2.LINE_AA,
                    False,
                )
                cv2.imshow("LOCK", canvas)
                cv2.waitKey(1)
            elif evt.type is EventType.FACE:
                ready = False
                face = evt.data.data
                user = "Recognizing..."
                color = (0, 0, 0)
            elif evt.type is EventType.RESET:
                ready = True
            elif evt.type is EventType.RECOGNITION:
                result = evt.data
                if isinstance(result, str):
                    color = (0, 100, 0)
                    user = result
                else:
                    color = (0, 0, 100)
                    user = "Server Error" if result is None else result.name

    task = threading.Thread(target=task_, daemon=True)
    task.start()
    return lambda f: rx.put(f)


def subscribe(stream, type, *chans):
    def task_():
        for frame in stream:
            [chan(Event(type=type, data=frame)) for chan in chans]

    task = threading.Thread(target=task_, daemon=True)
    task.start()


def main():
    event_bus = queue.Queue()

    gesture_chan = gesture_task(event_bus)
    auth_chan = auth_task(event_bus)
    face_chan = face_task(event_bus)
    ui_chan = ui_task()

    subscribe(video_stream(), EventType.CAMERA_FRAME, ui_chan, gesture_chan)
    for evt in iter(event_bus.get, None):
        if evt.type is EventType.GESTURE:
            frames, restart = evt.data["frames"], evt.data["handle"]
            threading.Timer(
                5,
                lambda: (
                    restart.set(),
                    ui_chan(Event(type=EventType.RESET, data=None)),
                ),
            ).start()
            face_chan(frames)
        elif evt.type is EventType.FACE:
            ui_chan(evt)
            auth_chan(evt)
        elif evt.type is EventType.RECOGNITION:
            ui_chan(evt)


if __name__ == "__main__":
    main()
