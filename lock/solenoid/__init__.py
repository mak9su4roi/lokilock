import os

if os.environ.get("RPI", None) is not None:
    from .raspberry import API
else:
    from .laptop import API