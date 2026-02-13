from abc import ABC, abstractmethod
import numpy as np


class PreviewObject3D(ABC):
    """
    미리보기에 사용되는 모든 3D 객체의 공통 인터페이스
    """

    @abstractmethod
    def get_vertices(self) -> np.ndarray:
        """
        Returns:
            np.ndarray shape (N, 3)
        """
        pass

    @abstractmethod
    def get_edges(self) -> list[tuple[int, int]]:
        """
        Returns:
            [(i, j), ...]  where i,j are vertex indices
        """
        pass
