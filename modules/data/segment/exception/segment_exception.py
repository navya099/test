from execption.base_exception import BaseError
from data.segment.exception.error_code import SEGErrorCode

class SegmentException(BaseError):
    pass

class SegmentListNullError(SegmentException):
    """세그먼트 리스트 비어있는 오류"""
    def __init__(self):

        super().__init__("세그먼트 리스트가 비어있습니다.",code=SEGErrorCode.SEGMENT_LIST_NULL)

class InvalidSegmentTypeError(SegmentException):
    """잘못된 세그먼트 타입 사용 시"""
    def __init__(self, seg_type):
        super().__init__(f"지원하지 않는 세그먼트 타입: {seg_type}", code=SEGErrorCode.INVALID_SEGMENT_TYPE)

class InvalidSegmentError(SegmentException):
    """잘못된 세그먼트 객체 존재시"""
    def __init__(self, seg):
        super().__init__(f"세그먼트 객체가 유효하지 않습니다.: {seg.id}", code=SEGErrorCode.INVALID_SEGMENT)

class SegmentOverlapError(SegmentException):
    """세그먼트가 겹치거나 연결이 이상할 때"""
    def __init__(self):
        super().__init__("세그먼트가 겹치거나 연결이 올바르지 않습니다.", code=SEGErrorCode.SEGMENT_OVERLAP)

class SegmentNotFoundError(SegmentException):
    """찾으려는 세그먼트가 존재하지 않을 때"""
    def __init__(self):
        super().__init__(f"세그먼트를 찾을 수 없습니다:", code=SEGErrorCode.SEGMENT_NOT_FOUND)

class InvalidRadiusError(SegmentException):
    """세그먼트 내부 곡선 반경이 잘못된 경우"""
    def __init__(self, radius: float):
        super().__init__(f"곡선 반경이 유효하지 않습니다: {radius}", code=SEGErrorCode.INVALID_RADIUS)

class InvalidPointError(SegmentException):
    """직선 좌표가 잘못된 경우"""
    def __init__(self, point):
        super().__init__(f"직선 좌표가 유효하지 않습니다: {point}", code=SEGErrorCode.INVALID_POINT)

class SegmentEmptyError(SegmentException):
    """세그먼트 길이가 0인 경우"""
    def __init__(self, seg_id):
        super().__init__(f"세그먼트 길이가 0입니다: {seg_id}", code=SEGErrorCode.SEGMENT_EMPTY)

class SegmentConnectionError(SegmentException):
    """세그먼트 연결이 올바르지 않은 경우"""
    def __init__(self, seg_id):
        super().__init__(f"세그먼트 연결 오류 발생: {seg_id}", code=SEGErrorCode.INVALID_CONNETION)

class SegmentDuplicateError(SegmentException):
    """중복 세그먼트 존재"""
    def __init__(self, seg_id):
        super().__init__(f"중복 세그먼트 발견: {seg_id}", code=SEGErrorCode.SEGMENT_DUPLICATE)
