import queue
import threading
import time
from contextlib import contextmanager

import picamera2

from common.types.frame import Frame


@contextmanager
def camera_stream():
    stop = threading.Event()
    camera = picamera2.Picamera2()
    camera.configure(camera.create_still_configuration({"size": (512, 512)}))
    frames = queue.Queue()

    def producer():
        while not stop.is_set():
            frames.put(Frame(image=camera.capture_image(), timestamp=time.time()))
            time.sleep(0.3)
        frames.put(None)

    try:
        camera.start()
        threading.Thread(target=producer, daemon=True).start()
        yield frames
    except KeyboardInterrupt:
        stop.set()
        print("CLOSING..")
    finally:
        camera.close()
