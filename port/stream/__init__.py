import os


if os.environ.get("RPI", None) is not None:
    from .pi import stream
else:
    from .laptop import stream
