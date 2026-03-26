from abc import ABC, abstractmethod
from model.grade.vipdata import VIPdata

class VIPDATABuilder(ABC):
    """추상 VIP데이터 빌더"""
    @abstractmethod
    def build(self, data, brokenchain) -> list[VIPdata]:
        raise NotImplementedError

    @abstractmethod
    def preprocess(self, data, brokenchain) -> VIPdata:
        raise NotImplementedError