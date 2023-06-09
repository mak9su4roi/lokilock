from .. import RASPBERRY_PI

if RASPBERRY_PI:
    from .raspberry import API
else:
    from .laptop import API