from enum import Enum, auto

class SEGErrorCode(Enum):
    GENERIC = auto()

    # Segment 관련
    SEGMENT_LIST_NULL = auto()
    INVALID_SEGMENT_TYPE = auto()
    INVALID_SEGMENT = auto()
    SEGMENT_OVERLAP = auto()
    SEGMENT_NOT_FOUND = auto()
    INVALID_RADIUS = auto()
    INVALID_POINT = auto()
    SEGMENT_EMPTY = auto()
    INVALID_CONNETION = auto()
    SEGMENT_DUPLICATE = auto()
