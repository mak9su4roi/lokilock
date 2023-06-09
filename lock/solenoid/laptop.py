from time import sleep
import threading


class API:
    def _open(self, duration: float):
        print("Oppened")
        sleep(duration)
        print("Closed")
    
    def open(self, duration: float):
        threading.Thread(target=lambda: self._open(duration=duration), daemon=True).start()
