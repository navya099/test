# gui/result_table.py

import tkinter as tk
from tkinter import ttk


class ResultTable(ttk.LabelFrame):

    def __init__(self, parent):
        super().__init__(
            parent,
            text="경매장 매물 비교"
        )

        self.columns = [
            "rank",
            "name",
            "price",
            "tax",
            "actual_price",
            "flame",
            "scroll",
            "potential",
            "additional",
            "damage",
            "difference",
            "price_difference",
            "remaining",
            "efficiency",
        ]

        self.headers = {
            "rank": "순위",
            "name": "이름",
            "price": "판매가",
            "tax": "관세",
            "actual_price": "실구매가",
            "flame": "추옵",
            "scroll": "작",
            "potential": "잠재",
            "additional": "에디",
            "damage": "환산 최종뎀",
            "difference": "기준 대비",
            "price_difference": "가격차",
            "remaining": "잔여 가횟",
            "efficiency": "가성비",
        }

        self.tree = ttk.Treeview(
            self,
            columns=self.columns,
            show="headings"
        )

        for column in self.columns:

            self.tree.heading(
                column,
                text=self.headers[column]
            )

            self.tree.column(
                column,
                width=100,
                anchor="center"
            )

        self.tree.column(
            "rank",
            width=50
        )

        self.tree.column(
            "name",
            width=150
        )

        self.tree.column(
            "flame",
            width=170
        )

        self.tree.column(
            "scroll",
            width=170
        )

        self.tree.column(
            "potential",
            width=100
        )

        self.tree.column(
            "additional",
            width=180
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

    # ========================================================
    # 전체 삭제
    # ========================================================

    def clear(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

    # ========================================================
    # 선택
    # ========================================================

    def get_selected_index(self):

        selected = self.tree.selection()

        if not selected:
            return None

        item_id = selected[0]

        return self.tree.index(item_id)

    # ========================================================
    # 결과 표시
    # ========================================================

    def show_results(
        self,
        results,
        base,
        calculator,
        character
    ):

        self.clear()

        base_damage = calculator.final_damage(
            base,
            character
        )

        for rank, item in enumerate(
            results,
            start=1
        ):

            damage = calculator.final_damage(
                item,
                character
            )

            difference = (
                damage
                - base_damage
            )

            price_difference = (
                item.actual_price
                - base.actual_price
            )

            efficiency = calculator.efficiency_score(
                item,
                base,
                character
            )

            if efficiency == float("inf"):
                efficiency_text = "∞"
            else:
                efficiency_text = (
                    f"{efficiency:.4f}"
                )

            tax_text = "O" if item.tax else "X"

            values = [
                rank,
                item.name,

                f"{item.price:.1f}억",

                tax_text,

                f"{item.actual_price:.1f}억",

                item.flame_text(),

                item.scroll_text(),

                item.potential_text(),

                item.additional_text(),

                f"{damage:.3f}%",

                f"{difference:+.3f}%",

                f"{price_difference:+.1f}억",

                f"{item.remaining_count}/{item.max_count}",

                efficiency_text,
            ]

            self.tree.insert(
                "",
                "end",
                values=values
            )