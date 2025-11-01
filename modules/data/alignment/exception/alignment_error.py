# Alignment 관련
from execption.base_exception import BaseError
from data.alignment.exception.error_code import ALErrorCode

class AlignmentError(BaseError):
    pass

class InvalidGeometryError(AlignmentError):
    def __init__(self, reason: str):
        super().__init__(f"솔루션을 해결할 수 없습니다: {reason}", code=ALErrorCode.GEOM_INVALID)

class RadiusError(AlignmentError):
    def __init__(self, radius: float):
        super().__init__(f"곡선 반경이 유효하지 않음: {radius}", code=ALErrorCode.RADIUS_ERROR)

class GroupNullError(AlignmentError):
    def __init__(self, group):
        super().__init__(f"그룹이 비어있습니다: {group.id}", code=ALErrorCode.GROUP_NULL)

class NotEnoughPIPointError(AlignmentError):
    def __init__(self):
        super().__init__("선형 생성할 PI 수가 부족합니다.", code=ALErrorCode.NOT_ENOUGH_PI)

class SegmentMismatchError(AlignmentError):
    def __init__(self):
        super().__init__("그룹과 세그먼트 간 매칭이 올바르지 않습니다.", code=ALErrorCode.SEGMENT_MISMATCH)

class PIOutOfRangeError(AlignmentError):
    def __init__(self, index):
        super().__init__(f"PI 인덱스가 범위를 벗어났습니다: {index}", code=ALErrorCode.PI_OUT_OF_RANGE)

class CurveCreationError(AlignmentError):
    def __init__(self, index):
        super().__init__(f"곡선 생성 실패: {index}", code=ALErrorCode.CURVE_CREATION_FAILED)

class DuplicatePIError(AlignmentError):
    def __init__(self, index):
        super().__init__(f"중복 PI 발견: {index}", code=ALErrorCode.DUPLICATE_PI)

class OVER180IAError(AlignmentError):
    def __init__(self, index):
        super().__init__(f"IA는 180도를 넘을 수 없습니다.: {index}", code=ALErrorCode.OVER_180_PI)

class PointNotEmpty(AlignmentError):
    def __init__(self, point):
        super().__init__(f"지정한 측점에서 좌표를 찾을 수 없습니다.: {point}", code=ALErrorCode.POINT_NOT_EMPTY)

class StationOutOfRange(AlignmentError):
    def __init__(self, station):
        super().__init__(f"지정한 측점이 선형을 벗어났습니다.: {station}", code=ALErrorCode.STA_OUT_OF_RANGE)

class NoUpdatePIError(AlignmentError):
    def __init__(self, index):
        super().__init__(f"첫번째 PI와 마지막 PI는 변경할 수 없습니다.: {index}", code=ALErrorCode.NO_UPDATE_PI)

class NoDeletePIError(AlignmentError):
    def __init__(self, index):
        super().__init__(f"첫번째 PI와 마지막 PI는 삭제할 수 없습니다.: {index}", code=ALErrorCode.NO_DELETE_PI)
