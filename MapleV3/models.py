# ============================================================
# models.py
# ============================================================

from dataclasses import dataclass


@dataclass
class Item:
    """
    아이템의 기본 입력 정보
    """

    name: str

    # 아이템 레벨
    item_level: int

    # 기본 아이템 가격
    # 예: 노작 도미 17억
    base_price: float

    # 잠재 깡통 / 토드용 아이템 가격
    # 예: 유니크 + 에디 토드용 도미 15억
    potential_blank_price: float

    # 현재 스타포스
    current_star: int

    # 목표 스타포스
    target_star: int

    # 완제품 가격
    finished_price: float

    # 강화권
    # None = 없음
    # 17 = 17성권
    # 18 = 18성권
    coupon_star: int | None = None

    # 관세 적용 여부
    base_has_tariff: bool = True
    blank_has_tariff: bool = True
    finished_has_tariff: bool = True


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
    """
    하나의 제작/구매 루트 결과
    """

    name: str
    total_cost: float

    starforce_cost: float = 0.0
    destroy: float = 0.0
    attempt: float = 0.0