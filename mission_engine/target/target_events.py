from enum import Enum, auto

class TargetEvent(Enum):
    NONE = auto()
    TARGET_CANDIDATE = auto()
    TARGET_CONFIRMED = auto()
    TARGET_LOST = auto()
