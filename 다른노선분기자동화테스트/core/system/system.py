import abc

class System(abc.ABC):
    """모든 시스템의 추상 클래스"""

    @abc.abstractmethod
    def execute(self, entities, components):
        """엔티티와 컴포넌트를 받아 처리"""
        raise NotImplementedError
