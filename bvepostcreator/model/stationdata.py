from dataclasses import dataclass, field


@dataclass
class StationData:
    """측점 보관 데이터클래스
    Attributes:
        origin_sta: 원래 측점
        after_sta: 변경후 측점
    """
    origin_sta: float = 0.0
    after_sta: float = field(default=None)

    def __post_init__(self):
        if self.after_sta is None:
            self.after_sta = self.origin_sta
    @property
    def difference(self):
        """측점 차"""
        return self.after_sta - self.origin_sta
