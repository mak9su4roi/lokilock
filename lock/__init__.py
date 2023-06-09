import os
from typing import Final

RASPBERRY_PI: Final = os.environ.get("RPI", None) is not None