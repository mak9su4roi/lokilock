from enum import IntEnum, auto


class EventType(IntEnum):
    CAMERA_FRAME = auto()
    ACTIVATION_FRAMES = auto()

    ACTIVATION_REQ = auto()
    ACTIVATION_RSP = auto()

    DETECTION_REQ = auto()
    DETECTION_RSP = auto()

    VERIFICATION_REQ = auto()
    VERIFICATION_RSP = auto()
