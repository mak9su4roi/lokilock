import threading
from time import time

from lock import solenoid
from lock.tasks import activation, camera, detection, verification, lui
from lock.tasks.constants import EventType
from lock.tasks.task import Event, Router, UniDirChannel
from lock.settings import RASPBERRY_PI, UNLOCK_INTERVAL


if __name__ == "__main__":
    main_bus = UniDirChannel()
    router = Router()
    camera = camera.task()
    detection = detection.task()
    activation = activation.task()
    verification = verification.task()

    extra = ([] if RASPBERRY_PI else [lui.task()])
    router.subscribe(camera, activation.tx, *extra)
    router.subscribe(activation.rx, main_bus.tx, *extra)
    router.subscribe(detection.rx, main_bus.tx, *extra)
    router.subscribe(verification.rx, main_bus.tx, *extra)

    activation.tx(Event(type=EventType.ACTIVATION_REQ))
    solenoid = solenoid.API()

    print(10)
    for evt in iter(main_bus.rx, None):
        if evt.type is EventType.ACTIVATION_FRAMES:
            t = time()
            print("Detected activation gesture")
            detection.tx(Event(type=EventType.DETECTION_REQ, data=evt.data))
        if evt.type is EventType.DETECTION_RSP:
            if evt.data is None:
                activation.tx(Event(type=EventType.ACTIVATION_REQ))
            else:
                verification.tx(Event(type=EventType.VERIFICATION_REQ, data=evt.data))
        if evt.type is EventType.VERIFICATION_RSP:
            print(evt)
            print(f"VERIFICATION {time()-t}")
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

