import threading
from typing import Final

from lock import solenoid
from lock.tasks import activation, camera, detection, lui, verification
from lock.tasks.constants import EventType
from lock.tasks.task import Event, Router, UniDirChannel

UNLOCK_INTERVAL: Final = 5



if __name__ == "__main__":
    main_bus = UniDirChannel()
    router = Router()
    lui = lui.task()
    camera = camera.task()
    detection = detection.task()
    activation = activation.task()
    verification = verification.task()

    router.subscribe(camera, lui, activation.tx)
    router.subscribe(activation.rx, main_bus.tx, lui)
    router.subscribe(detection.rx, main_bus.tx, lui)
    router.subscribe(verification.rx, main_bus.tx, lui)

    activation.tx(Event(type=EventType.ACTIVATION_REQ))
    solenoid = solenoid.API()

    for evt in iter(main_bus.rx, None):
        if evt.type is EventType.ACTIVATION_FRAMES:
            print("Detected activation gesture")
            detection.tx(Event(type=EventType.DETECTION_REQ, data=evt.data))
        if evt.type is EventType.DETECTION_RSP:
            if evt.data is None:
                activation.tx(Event(type=EventType.ACTIVATION_REQ))
            else:
                verification.tx(Event(type=EventType.VERIFICATION_REQ, data=evt.data))
        if evt.type is EventType.VERIFICATION_RSP:
            print(evt)
            if isinstance(evt.data, str):
                solenoid.open(UNLOCK_INTERVAL)
                threading.Timer(
                    interval=UNLOCK_INTERVAL,
                    function=lambda: activation.tx(Event(type=EventType.ACTIVATION_REQ))
                ).start()
            else:
                threading.Timer(
                    interval=1,
                    function=lambda: activation.tx(Event(type=EventType.ACTIVATION_REQ))
                ).start()

