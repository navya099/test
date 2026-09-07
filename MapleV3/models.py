# ============================================================
# models.py
# ============================================================

from dataclasses import dataclass


@dataclass
class Item:
    name: str
    item_level: int

    # 기본 아이템 가격
    base_price: float

    # 잠재 깡통 / 토드용 아이템 가격
    potential_blank_price: float

    # 현재 스타포스
    current_star: int

    # 목표 스타포스
    target_star: int

    # 현재 잠재
    current_potential: int

    # 목표 잠재
    target_potential: int

    # 강화권
    coupon_star: int | None = None

    # 관세
    base_has_tariff: bool = True
    blank_has_tariff: bool = True


# ============================================================
# 완제품 경매장 매물
# ============================================================

@dataclass
class FinishedItem:

    star: int
    potential: int
    price: float

    has_tariff: bool = True

@dataclass
class StarforceResult:
    """
    스타포스 강화 계산 결과
    """

    cost: float
    destroy: float
    attempt: float


@dataclass
class RouteResult:

    name: str

    # 기본 제작비
    base_craft_cost: float

    # 스타포스 비용
    starforce_cost: float

    # 최종 총 비용
    total_cost: float

    # 스타포스 부가 정보
    destroy: float = 0.0
    attempt: float = 0.0

    # 완제품 매물 정보
    finished_item: FinishedItem | None = None