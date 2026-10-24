from Structure.bridge import Bridge
from Structure.structure import Structure
from Structure.tunnel import Tunnel


class StructureFactory:
    """구조물 객체를 생성하는 팩토리 클래스"""
    registry = {
        '교량': Bridge,
        '터널': Tunnel,
    }

    @classmethod
    def create_structure(cls, structuretype: str, name: str, startsta: float, endsta: float) -> Structure:
        """구조물 생성 팩토리메서드"""
        if structuretype not in cls.registry:
            raise ValueError(f"지원하지 않는 구조물 타입입니다: {structuretype}")
        return cls.registry[structuretype](name, startsta, endsta)