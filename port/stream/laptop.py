import queue
import threading

from common.types.frame import Frame


def stream(max_latency: float = 0.1) -> list[Frame]:
    import cv2

    buffer = queue.Queue(maxsize=1000)

    def shoot():
        vid = cv2.VideoCapture(0)
        while True:
            _, frame = vid.read()
            if frame is not None:
                frame = Frame(data=frame)
                buffer.put(frame)

    task = threading.Thread(target=shoot)
    task.start()

    while True:
        yield buffer.get()
