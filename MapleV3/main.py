# ============================================================
# 직작 완제구매 비교 프로그램
# ============================================================

from models import Item, FinishedItem
from calculator import (
    calculate_all_routes,
    get_best_route,
)


def print_result(
    item: Item,
    finished_items: list[FinishedItem],
):

    print()
    print("=" * 70)
    print(f"아이템 : {item.name}")
    print(
        f"목표   : "
        f"{item.target_star}성 / "
        f"{item.target_potential}%"
    )
    print("=" * 70)

    routes = calculate_all_routes(
        item,
        finished_items,
    )

    routes.sort(
        key=lambda route: route.total_cost
    )

    for index, route in enumerate(routes, start=1):

        print()
        print(
            f"[{index}위] {route.name}"
        )

        # ----------------------------------------------------
        # 완제품
        # ----------------------------------------------------

        if route.finished_item is not None:

            print(
                f"완제품 가격 : "
                f"{route.total_cost:.2f}억"
            )

        # ----------------------------------------------------
        # 제작 루트
        # ----------------------------------------------------

        else:

            print(
                f"기본 제작비 : "
                f"{route.base_craft_cost:.2f}억"
            )

            print(
                f"스타포스    : "
                f"{route.starforce_cost:.2f}억"
            )

            print(
                f"총 비용     : "
                f"{route.total_cost:.2f}억"
            )

            if route.starforce_cost > 0:

                print(
                    f"평균 파괴   : "
                    f"{route.destroy:.2f}회"
                )

                print(
                    f"평균 시도   : "
                    f"{route.attempt:.2f}회"
                )

    best = get_best_route(
        item,
        finished_items,
    )

    print()
    print("-" * 70)
    print(
        f"★ 추천 : {best.name}"
    )
    print(
        f"★ 최소 비용 : "
        f"{best.total_cost:.2f}억"
    )
    print("-" * 70)


# ============================================================
# 테스트
# ============================================================

dominator = Item(
    name="트와일라이트 마크",

    item_level=140,

    base_price=0.01,
    potential_blank_price=64,

    current_star=12,
    target_star=22,
    coupon_star=17,

    # 이미 네가 입력한 가격이 관세 포함이라면
    # False로 변경
    base_has_tariff=False,
    blank_has_tariff=False,

    current_potential=9,
    target_potential=27,
)

# ============================================================
# 경매장 완제품 매물
# ============================================================

finished_items = [

    FinishedItem(
        star=17,
        potential=15,
        price=5.00,
        has_tariff=False,
    ),

    FinishedItem(
        star=18,
        potential=15,
        price=5.10,
        has_tariff=False,
    ),

    FinishedItem(
        star=17,
        potential=18,
        price=6.20,
        has_tariff=False,
    ),

    FinishedItem(
        star=18,
        potential=18,
        price=6.00,
        has_tariff=False,
    ),

    FinishedItem(
        star=17,
        potential=21,
        price=12.00,
        has_tariff=False,
    ),

    FinishedItem(
        star=18,
        potential=21,
        price=13.00,
        has_tariff=False,
    ),

    FinishedItem(
        star=18,
        potential=24,
        price=13.70,
        has_tariff=False,
    ),
FinishedItem(
        star=21,
        potential=27,
        price=88,
        has_tariff=False,
    ),
]

print_result(dominator, finished_items=finished_items)