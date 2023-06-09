import threading
from time import sleep
from typing import Final

import RPi.GPIO as GPIO


class API:
    RELAY_PIN: Final = 26
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RELAY_PIN, GPIO.OUT)
        GPIO.output(self.RELAY_PIN, 1)
    
    def _open(self, duration: float):
        print("Oppened")
        GPIO.output(self.RELAY_PIN, 0)
        sleep(duration)
        GPIO.output(self.RELAY_PIN, 1)
    
    def open(self, duration: float):
        threading.Thread(target=lambda: self._open(duration=duration), daemon=True).start()


