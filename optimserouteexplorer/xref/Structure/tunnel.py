from .structure import Structure


class Tunnel(Structure):
    """터널 클래스 (Structure상속)
    """

    def __init__(self, name: str, startsta: float, endsta: float):
        super().__init__(name, '터널', startsta, endsta)