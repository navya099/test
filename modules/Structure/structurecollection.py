from Structure.structure import Structure
from logger import logger

class StructureCollection(list):
    """구조물들을 컬렉션하는 클래스(리스트 상속)"""

    def __init__(self):
        super().__init__()

    def get_by_type(self, structuretype: str) -> list[Structure]:
        """구조물을 타입별로 얻기"""
        return [s for s in self if s.structuretype == structuretype]

    def find_containing(self, targetsta: float) -> Structure | None:
        """targetsta가 포함된 첫 번째 구조물을 반환"""
        for s in self:
            if s.isstructure(targetsta):
                return s
        return None  # 없을 경우 None 반환

    def all_structures(self) -> list[Structure]:
        """모든 구조물 리스트 반환"""
        return list(self)  # self 자체가 리스트이므로 그대로 반환

    def get_structure_type_at(self, sta: float) -> str:
        """
        주어진 위치 sta가 교량, 터널, 토공인지 판별하는 메서드.

        :param sta: 위치 (거리값)
        :return: '교량', '터널', 또는 '토공'
        """
        try:
            structure = self.find_containing(sta)
            if structure:
                return structure.structuretype

        except Exception as ex:

            logger.error(
                f"structure lookup failed: {type(ex).__name__} - {ex} | sta={sta}")
        return '토공'