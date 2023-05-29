import time

import numpy as np
from pydantic import Field

from .model import Model


class Timestamp(Model):
    timestamp: float = Field(default_factory=time.time)


class Frame(Timestamp):
    data: np.ndarray
