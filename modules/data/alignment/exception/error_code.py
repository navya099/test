from enum import Enum, auto

class ALErrorCode(Enum):
    GENERIC = auto()

    # Alignment 관련
    GEOM_INVALID = auto()
    RADIUS_ERROR = auto()
    GROUP_NULL = auto()
    NOT_ENOUGH_PI = auto()
    SEGMENT_MISMATCH = auto()
    PI_OUT_OF_RANGE = auto()
    CURVE_CREATION_FAILED = auto()
    DUPLICATE_PI = auto()
    OVER_180_PI = auto()
    POINT_NOT_EMPTY = auto()
    STA_OUT_OF_RANGE = auto()
    NO_UPDATE_PI = auto()
    NO_DELETE_PI = auto()
