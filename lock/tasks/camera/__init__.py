import os

if os.environ.get("RPI", None) is not None:
    from .raspberry import task
else:
    from .laptop import task
