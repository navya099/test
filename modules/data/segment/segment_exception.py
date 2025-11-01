class AlignmentError(Exception):
    """기본 선형 생성 오류"""

    def __init__(self, message: str, code: str = "GENERIC"):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return f"[{self.code}] {self.args[0]}"


class InvalidGeometryError(AlignmentError):
    """좌표 관계나 반경이 잘못된 경우"""

    def __init__(self, reason: str):
        super().__init__(f"해결할 수 없는 선형 구성: {reason}", code="GEOM_INVALID")


class RadiusError(AlignmentError):
    """곡선 반경 관련 오류"""

    def __init__(self, radius: float):
        super().__init__(f"곡선 반경이 유효하지 않음: {radius}", code="RADIUS_ERROR")
