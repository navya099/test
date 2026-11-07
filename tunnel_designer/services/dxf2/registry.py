"""타입 → 빌더 레지스트리. (기존 services/dxf.registry 그대로 사용)"""
from __future__ import annotations
from typing import Callable

from core.constants import TunnelType

Builder = Callable[..., None]
_REGISTRY: dict[TunnelType, Builder] = {}


def register(kind: TunnelType):
    """@register(TunnelType.BOX) 데코레이터."""
    def _wrap(fn):
        _REGISTRY[kind] = fn
        return fn
    return _wrap


def get_builder(kind: TunnelType) -> Builder:
    if kind not in _REGISTRY:
        raise NotImplementedError(
            f"{kind.value} 타입의 DXF 빌더가 아직 등록되지 않았습니다.")
    return _REGISTRY[kind]


def list_registered() -> list[TunnelType]:
    return list(_REGISTRY.keys())