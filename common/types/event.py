from time import time
from enum import Enum
from typing import Any, Optional

from .model import Model
from pydantic import Field


class Timestamp(Model):
    timestamp: float = Field(default_factory=time)

class Event(Timestamp):
    type: Enum
    data: Optional[Any]
