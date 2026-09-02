#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메이플스토리 아이템 가성비 계산기
- 옵션 % 대비 가격 효율(억/%) 계산
- 관세 10% 자동 반영
- 완제품 vs 자가제작(직작+스타포스) 비교

사용법: 아래 items 리스트만 매번 수정해서 실행하면 됩니다.
    python3 maple_item_calc.py
"""

from dataclasses import dataclass, field
from typing import Optional


# ----------------------------------------------------------------------
# 1. 아이템 정의
#    percent: 총 스탯 % (INT/올스탯/유니크E/레전L 등은 동일 가중치로 환산해서 입력)
#    price_eok: 표시 가격 (억 단위)
#    tariff: 관세 여부 (True면 10% 추가)
#    label: 구분용 이름
# ----------------------------------------------------------------------

@dataclass
class Item:
    label: str
    percent: float          # 총 % (환산치)
    price_eok: float        # 표시가 (억)
    tariff: bool = False    # 관세 여부
    tariff_rate: float = 0.10

    @property
    def real_price(self) -> float:
        """관세 반영 실구매가 (억)"""
        return self.price_eok * (1 + self.tariff_rate) if self.tariff else self.price_eok

    @property
    def efficiency(self) -> float:
        """억 / % (낮을수록 가성비 좋음)"""
        if self.percent == 0:
            return float("inf")
        return self.real_price / self.percent


@dataclass
class SelfMade:
    """자가제작(직작) 정보 - 완제품과 비교할 때 사용"""
    base_item: Item                 # 비완제품 가격 정보
    starforce_cost_eok: float = 0.0  # 스타포스 기댓값 (억), 필요 없으면 0


def print_ranking(items: list[Item], title: str = "가성비 순위"):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    print(f"{'이름':<28}{'총%':>6}{'실구매가(억)':>14}{'억/%':>10}")
    print("-" * 60)

    ranked = sorted(items, key=lambda x: x.efficiency)
    for i, it in enumerate(ranked, 1):
        star = " ⭐" if i == 1 else ""
        print(f"{it.label:<28}{it.percent:>6.1f}{it.real_price:>14.2f}{it.efficiency:>10.3f}{star}")
    print()


def compare_self_vs_complete(pairs: list[tuple[str, SelfMade, Item]]):
    """
    자가제작 총비용(비완제품가 + 스타포스 기댓값) vs 완제품가 비교
    pairs: (이름, SelfMade, 완제품 Item) 리스트
    """
    print(f"\n{'='*70}")
    print(" 완제품 vs 자가제작 비교")
    print(f"{'='*70}")
    print(f"{'이름':<20}{'자가제작총액':>14}{'완제품가':>12}{'차액(완제품기준)':>18}")
    print("-" * 70)

    for name, self_made, complete in pairs:
        self_total = self_made.base_item.real_price + self_made.starforce_cost_eok
        diff = self_total - complete.real_price
        verdict = "완제품이 유리" if diff > 0 else "자가제작이 유리" if diff < 0 else "동일"
        print(f"{name:<20}{self_total:>14.2f}{complete.real_price:>12.2f}"
              f"{f'{abs(diff):.2f}억 ({verdict})':>25}")
    print()


# ----------------------------------------------------------------------
# 2. 예시: 매번 여기 리스트만 갈아끼우면 됩니다
# ----------------------------------------------------------------------

if __name__ == "__main__":

    # --- 예시 1: 일반 옵션 비교 (레전 상의류) ---
    top_items = [
        Item("유니크 2줄 17%",          17, 9,      tariff=False),
        Item("유니크 3줄 24%",          24, 31.99,  tariff=False),
        Item("레전드리 2줄 20%",        20, 24,     tariff=False),
        Item("레전드리 2줄 23%",        23, 28,     tariff=False),
        Item("레전드리 2줄 26%",        26, 42,     tariff=False),
        Item("레전드리 3줄 24%",        24, 45,     tariff=False),
        Item("레전드리 3줄 27%",        27, 70,     tariff=False),
        Item("레전드리 3줄 33%",        33, 177,    tariff=False),
    ]
    print_ranking(top_items, "상의 아이템 가성비")

    # --- 예시 2: 관세 아이템 (신발 완제품) ---
    shoe_items = [
        Item("유니크 2줄 15% 18성",  15, 20, tariff=True),
        Item("유니크 3줄 21% 18성",  21, 41, tariff=True),
        Item("레전 2줄 21% 18성",    21, 37, tariff=True),
        Item("레전 3줄 30% 18성",    30, 88, tariff=True),
    ]
    print_ranking(shoe_items, "신발 완제품 가성비")

    # --- 예시 3: 완제품 vs 자가제작 비교 (견장) ---
    STARFORCE_18 = 17  # 억, 18성 기댓값

    pairs = [
        (
            "유니크 2줄 15%",
            SelfMade(Item("유니크2줄 비완제", 15, 7, tariff=True), STARFORCE_18),
            Item("유니크2줄 완제 18성", 15, 20, tariff=True),
        ),
        (
            "레전 2줄 21%",
            SelfMade(Item("레전2줄 비완제", 21, 35, tariff=True), STARFORCE_18),
            Item("레전2줄 완제 18성", 21, 40, tariff=True),
        ),
        (
            "유니크 3줄 21%",
            SelfMade(Item("유니크3줄 비완제", 21, 28, tariff=True), STARFORCE_18),
            Item("유니크3줄 완제 18성", 21, 40, tariff=True),
        ),
    ]
    compare_self_vs_complete(pairs)