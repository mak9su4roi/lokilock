from enum import Enum
from typing import Any

from .model import Model


class Event(Model):
    type: Enum
    data: Any
