from dataclasses import dataclass


# ============================================================
# 설정
# ============================================================

TARIFF_RATE = 1.1
ENHANCE_EXPECTED_COST = 17.0
SCROLL_COUNT = 3


# ============================================================
# Item
# ============================================================

@dataclass
class Item:
    name: str

    # 현재 아이템 판매가
    current_price: float

    # 18성 완제품 판매가
    finished_price: float

    # 관세 적용 여부
    has_tariff: bool = True


# ============================================================
# 계산
# ============================================================

def apply_tariff(price, has_tariff):
    if has_tariff:
        return price * TARIFF_RATE

    return price


def calculate_item(item):
    # 현재 아이템 실질 가격
    current_cost = apply_tariff(
        item.current_price,
        item.has_tariff
    )

    # 18성 완제품 실질 가격
    finished_cost = apply_tariff(
        item.finished_price,
        item.has_tariff
    )

    # 직접 강화
    self_make_cost = current_cost + ENHANCE_EXPECTED_COST

    # 강화권 가치
    scroll_value = finished_cost - current_cost

    # 직접 강화 대비 강화권 사용 절약액
    self_make_saving = finished_cost - self_make_cost

    return {
        "item": item,
        "current_cost": current_cost,
        "finished_cost": finished_cost,
        "self_make_cost": self_make_cost,
        "scroll_value": scroll_value,
        "self_make_saving": self_make_saving,
    }


# ============================================================
# 최적화
# ============================================================

def optimize(items):
    results = [
        calculate_item(item)
        for item in items
    ]

    # 강화권 가치가 높은 순서
    results.sort(
        key=lambda x: x["scroll_value"],
        reverse=True
    )

    for i, result in enumerate(results):
        result["use_scroll"] = i < SCROLL_COUNT

    return results


# ============================================================
# 출력
# ============================================================

def print_result(results):

    print("=" * 80)
    print("18성 강화권 최적 배분")
    print("=" * 80)

    for result in results:
        item = result["item"]

        tariff_text = "적용" if item.has_tariff else "미적용"

        print(f"\n[{item.name}]")
        print(f"  관세       : {tariff_text}")
        print(f"  현재 판매가 : {item.current_price:.2f}억")
        print(f"  현재 실질가 : {result['current_cost']:.2f}억")
        print(f"  18성 판매가 : {item.finished_price:.2f}억")
        print(f"  18성 실질가 : {result['finished_cost']:.2f}억")
        print(f"  직접 강화비 : {result['self_make_cost']:.2f}억")
        print(f"  강화권 가치 : {result['scroll_value']:.2f}억")
        print(f"  직접 강화 대비 절약 : "
              f"{result['self_make_saving']:.2f}억")

        if result["use_scroll"]:
            print("  >>> 강화권 사용")
        else:
            print("  >>> 직접 강화")

    print("\n" + "=" * 80)

    scroll_items = [
        r["item"].name
        for r in results
        if r["use_scroll"]
    ]

    direct_items = [
        r["item"].name
        for r in results
        if not r["use_scroll"]
    ]

    print(f"강화권 사용 : {', '.join(scroll_items)}")
    print(f"직접 강화   : {', '.join(direct_items)}")
    print("=" * 80)


# ============================================================
# 아이템 입력
# ============================================================

items = [
    Item("장갑", 36.0, 60.0, True),
    Item("신발", 6.1, 30.0, True),
    Item("견장", 5.8, 33.0, True),

    # 이미 가지고 있는 망토 → 현재 구매가격 0
    Item("망토", 0.0, 30.0, True),
]


# ============================================================
# 실행
# ============================================================

results = optimize(items)
print_result(results)