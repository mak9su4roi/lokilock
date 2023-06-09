from collections import deque
from enum import IntEnum, auto
from typing import Optional
from time import time

import numpy as np

import models.handnet_gesture as gnet
from common.types.event import Event

from .helpers import event_stream
from . import task as _task
from .constants import EventType
from ..settings import GESTURE_RESET_INTERVAL, FRAMES_PER_GESTURE


class States(IntEnum):
    PROCESSING = auto()
    IDLE = auto()


class StreamGestureDetector:
    def __init__(self):
        self.__hand_opened = deque([], FRAMES_PER_GESTURE//2)
        self.__hand_closed = deque([], FRAMES_PER_GESTURE//2)
        self.__timestamp = time()
        self.__detector = gnet.load()

    def clear(self):
        self.__hand_opened.clear()
        self.__hand_closed.clear()

    def process(self, frame: np.ndarray, timestamp) -> Optional[list[np.ndarray]]:
        opened = self.__hand_opened
        closed = self.__hand_closed
        gesture = self.__detector(frame)
        if gesture is gnet.Gesture.NONE:
            return
        if timestamp - self.__timestamp > GESTURE_RESET_INTERVAL:
            self.clear()
        self.__timestamp = timestamp

        if gesture is gnet.Gesture.OPEN and not closed:
            opened.append(frame)
        elif gesture is gnet.Gesture.SQUEEZED and len(opened) == opened.maxlen:
            closed.append(frame)
        else:
            self.clear()

        if len(opened) == opened.maxlen and len(closed) == closed.maxlen:
            recorded_frames = (*opened, *closed)
            self.clear()
            return recorded_frames


@_task.shedule_bidir
def task(chan: _task.BiDirChannel):
    detector = StreamGestureDetector()
    state = States.IDLE

    for evt in event_stream(chan.rx):
        if state is States.PROCESSING and evt.type is EventType.CAMERA_FRAME:
            if activation_stream := detector.process(evt.data, evt.timestamp):
                chan.tx(Event(type=EventType.ACTIVATION_FRAMES, data=activation_stream))
                state = States.IDLE
        elif state is States.IDLE and evt.type is EventType.ACTIVATION_REQ:
            chan.tx(Event(type=EventType.ACTIVATION_RSP))
            state = States.PROCESSING
