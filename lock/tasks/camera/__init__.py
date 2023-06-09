from ... import RASPBERRY_PI

if RASPBERRY_PI:
    from .raspberry import task
else:
    from .laptop import task
