# core/system.py
import abc
import logging
from typing import Any, Dict


class System(abc.ABC):
    """모든 시스템의 추상 클래스. 파이프라인 계약(requires/produces)을 정의한다."""

    requires_entities: frozenset[str] = frozenset()
    produces_entities: frozenset[str] = frozenset()
    requires_components: frozenset[str] = frozenset()
    produces_components: frozenset[str] = frozenset()

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__module__)

    @abc.abstractmethod
    def execute(self, entities: Dict[str, Any], components: Dict[str, Any]) -> None:
        """엔티티와 컴포넌트를 받아 제자리에서 처리한다."""
        pass