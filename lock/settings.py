from pydantic import AnyUrl, BaseSettings
from typing import Final
from . import RASPBERRY_PI


class Settings(BaseSettings):
    lock_id: str
    verification_service_url: AnyUrl


UNLOCK_INTERVAL: Final = 5
GESTURE_RESET_INTERVAL: Final = 1.5 if RASPBERRY_PI else .5 
FRAMES_PER_GESTURE: Final = 4 if RASPBERRY_PI else 10
settings = Settings()