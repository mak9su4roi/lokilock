from time import time
from typing import Generator, Optional

from common.types.event import Event
from ..tasks.constants import EventType
from . import task


def event_stream(
    rx: task.Receiver, max_latency: float = 0.1
) -> Generator[Event, task.BiDirChannel, None]:
    evt: Optional[Event]
    while (evt := rx()) is not None:
        if evt.type is EventType.CAMERA_FRAME:
            if time() - evt.timestamp < max_latency:
                yield evt
            continue
        yield evt