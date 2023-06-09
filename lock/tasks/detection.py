import random

from common.types.event import Event
from models import blazeface

from . import task as _task
from .constants import EventType


def best_detection(faces):
    if faces:
        return random.choice(faces)

@_task.shedule_bidir
def task(chan: _task.BiDirChannel):
    detector = blazeface.load()
    for evt in iter(chan.rx, None):
        faces = [
            blazeface.crop(frame, res[0][0])
            for frame in evt.data
            if (res := detector(frame))
        ] 
        chan.tx(Event(type=EventType.DETECTION_RSP, data=best_detection(faces)))
