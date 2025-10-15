from dataclasses import dataclass


@dataclass
class Structure:
    """구조물 공통 기능을 관리하는 부모 클래스
            Attributes:
                name (str): 구조물 명칭
                structuretype (str): 구조물 종류(교량/터널)
                startsta(float): 시작 측점 m
                endsta(float): 끝 측점 m
            """
    name: str
    structuretype: str
    startsta: float
    endsta: float

    @property
    def length(self) -> float:
        """구조물 길이 length(endsta - startsta)"""
        return self.endsta - self.startsta

    def isstructure(self, targetsta: float) -> bool:
        """targetsta가 구조물 범위 내에 있는지 확인"""
        return self.startsta <= targetsta <= self.endsta

    def contains(self, targetsta: float) -> bool:
        """get_structure_type_if_contains호출을 위한 래퍼 메서드"""
        return self.isstructure(targetsta)

    def get_structure_type_if_contains(self, targetsta: float) -> str | None:
        """targetsta가 구조물 범위 내에 있는지 확인 후 타입 리턴"""
        if self.contains(targetsta):
            return self.structuretype
        return None

    def get_structure_stas(self) -> tuple[float, float]:
        """구조물의 시작 측점과 끝 측점 반환"""
        return self.startsta, self.endsta