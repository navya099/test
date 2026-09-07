# ============================================================
# calculator.py
# ============================================================

from config import TARIFF_RATE
from models import Item, StarforceResult, RouteResult, FinishedItem
from starforce_data import STARFORCE_TABLE


# ============================================================
# 기본 가격 처리
# ============================================================

def apply_tariff(price: float, has_tariff: bool) -> float:
    """
    관세 적용
    """

    if has_tariff:
        return price * TARIFF_RATE

    return price


# ============================================================
# 스타포스
# ============================================================

def get_starforce_step(
    item_level: int,
    star: int,
) -> StarforceResult:

    table = STARFORCE_TABLE[item_level]

    data = table[star]

    return StarforceResult(
        cost=data["cost"],
        destroy=data["destroy"],
        attempt=data["attempt"],
    )


def get_starforce_cost(
    item_level: int,
    start_star: int,
    target_star: int,
) -> StarforceResult:
    """
    start_star → target_star까지의 총 기대값
    """

    if target_star <= start_star:
        return StarforceResult(
            cost=0.0,
            destroy=0.0,
            attempt=0.0,
        )

    table = STARFORCE_TABLE[item_level]

    total_cost = 0.0
    total_destroy = 0.0
    total_attempt = 0.0

    for star in range(start_star, target_star):

        if star not in table:
            raise ValueError(
                f"{item_level}제 {star}→{star + 1}성 데이터가 없습니다."
            )

        data = table[star]

        total_cost += data["cost"]
        total_destroy += data["destroy"]
        total_attempt += data["attempt"]

    return StarforceResult(
        cost=total_cost,
        destroy=total_destroy,
        attempt=total_attempt,
    )


# ============================================================
# 제작 기본 비용
# ============================================================

def get_base_craft_cost(item: Item) -> float:

    base = apply_tariff(
        item.base_price,
        item.base_has_tariff,
    )

    blank = apply_tariff(
        item.potential_blank_price,
        item.blank_has_tariff,
    )

    return base + blank


# ============================================================
# 루트 1
# 깡통 + 직접 스타포스
# ============================================================

def calculate_direct_route(item: Item) -> RouteResult:

    craft_cost = get_base_craft_cost(item)

    starforce = get_starforce_cost(
        item.item_level,
        item.current_star,
        item.target_star,
    )

    return RouteResult(
        name="깡통 + 직접 강화",

        base_craft_cost=craft_cost,
        starforce_cost=starforce.cost,
        total_cost=craft_cost + starforce.cost,

        destroy=starforce.destroy,
        attempt=starforce.attempt,
    )


# ============================================================
# 루트 2
# 강화권 사용
# ============================================================

def calculate_coupon_route(
    item: Item,
) -> RouteResult | None:

    if item.coupon_star is None:
        return None

    coupon_star = item.coupon_star

    if coupon_star > item.target_star:
        return None

    craft_cost = get_base_craft_cost(item)

    # 강화권으로 목표 성 달성
    if coupon_star == item.target_star:

        return RouteResult(
            name=f"{coupon_star}성권 사용",

            base_craft_cost=craft_cost,
            starforce_cost=0.0,
            total_cost=craft_cost,
        )

    # 강화권 이후 추가 강화
    starforce = get_starforce_cost(
        item.item_level,
        coupon_star,
        item.target_star,
    )

    return RouteResult(
        name=f"{coupon_star}성권 + 추가 강화",

        base_craft_cost=craft_cost,
        starforce_cost=starforce.cost,
        total_cost=craft_cost + starforce.cost,

        destroy=starforce.destroy,
        attempt=starforce.attempt,
    )


# ============================================================
# 루트 3
# 완제품 구매
# ============================================================

# ============================================================
# 완제품 후보 필터
# ============================================================

def get_finished_candidates(
    item: Item,
    finished_items: list[FinishedItem],
) -> list[FinishedItem]:
    """
    목표 스타/잠재 이상을 만족하는 완제품만 반환
    """

    candidates = []

    for finished in finished_items:

        # 목표 스타 미만
        if finished.star < item.target_star:
            continue

        # 목표 잠재 미만
        if finished.potential < item.target_potential:
            continue

        candidates.append(finished)

    return candidates

def calculate_finished_routes(
    item: Item,
    finished_items: list[FinishedItem],
) -> list[RouteResult]:

    candidates = get_finished_candidates(
        item,
        finished_items,
    )

    routes = []

    for finished in candidates:

        price = apply_tariff(
            finished.price,
            finished.has_tariff,
        )

        routes.append(
            RouteResult(
                name=(
                    f"완제품 "
                    f"{finished.star}성 / "
                    f"{finished.potential}%"
                ),

                base_craft_cost=0.0,
                starforce_cost=0.0,
                total_cost=price,

                finished_item=finished,
            )
        )

    return routes


# ============================================================
# 전체 루트 계산
# ============================================================

def calculate_all_routes(
    item: Item,
    finished_items: list[FinishedItem],
) -> list[RouteResult]:

    routes = []

    # 직접 강화
    routes.append(
        calculate_direct_route(item)
    )

    # 강화권
    coupon_route = calculate_coupon_route(item)

    if coupon_route is not None:
        routes.append(coupon_route)

    # 완제품 여러 개
    routes.extend(
        calculate_finished_routes(
            item,
            finished_items,
        )
    )

    return routes


# ============================================================
# 최적 루트
# ============================================================

# ============================================================
# 최저가 추천
# ============================================================

def get_best_route(
    item: Item,
    finished_items: list[FinishedItem],
) -> RouteResult:

    routes = calculate_all_routes(
        item,
        finished_items,
    )

    return min(
        routes,
        key=lambda route: route.total_cost,
    )