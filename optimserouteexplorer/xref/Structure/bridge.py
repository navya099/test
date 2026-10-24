from .structure import Structure

class Bridge(Structure):
    """교량 클래스 (Structure상속)
    """

    def __init__(self, name: str, startsta: float, endsta: float):
        super().__init__(name, '교량', startsta, endsta)