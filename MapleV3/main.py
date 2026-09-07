# ============================================================
# 직작 완제구매 비교 프로그램
# ============================================================

from models import Item
from calculator import (
    calculate_all_routes,
    get_best_route,
)


def print_result(item: Item):

    print()
    print("=" * 60)
    print(f"아이템 : {item.name}")
    print("=" * 60)

    routes = calculate_all_routes(item)

    for route in routes:

        print()
        print(f"[{route.name}]")

        print(f"총 비용      : {route.total_cost:.2f}억")

        if route.starforce_cost > 0:
            print(
                f"강화 비용    : "
                f"{route.starforce_cost:.2f}억"
            )

            print(
                f"평균 파괴    : "
                f"{route.destroy:.2f}회"
            )

            print(
                f"평균 시도    : "
                f"{route.attempt:.2f}회"
            )

    best = get_best_route(item)

    print()
    print("-" * 60)
    print(
        f"★ 추천 : {best.name}"
    )
    print(
        f"★ 최소 비용 : {best.total_cost:.2f}억"
    )
    print("-" * 60)


# ============================================================
# 테스트
# ============================================================

dominator = Item(
    name="트와일라이트 마크",

    item_level=140,

    base_price=0.01,
    potential_blank_price=4.95,

    current_star=12,
    target_star=17,

    finished_price=6.7,

    coupon_star=17,

    # 이미 네가 입력한 가격이 관세 포함이라면
    # False로 변경
    base_has_tariff=False,
    blank_has_tariff=False,
    finished_has_tariff=True,
)


print_result(dominator)