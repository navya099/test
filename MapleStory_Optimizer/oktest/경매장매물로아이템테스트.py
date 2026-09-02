import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv


# =========================================================
# 효율 테이블
# =========================================================

EFF_TABLE = {
    "보총뎀": {"value": 40, "final": 5.350},
    "마력": {"value": 30, "final": 0.823},
    "마력%": {"value": 12, "final": 5.192},
    "크뎀": {"value": 8, "final": 3.082},
    "방무(300)": {"value": 40, "final": 0.763},
    "방무(380)": {"value": 40, "final": 0.971},
    "INT": {"value": 30, "final": 0.282},
    "INT%": {"value": 12, "final": 1.247},
    "%미반영 INT": {"value": 200, "final": 0.364},
    "LUK": {"value": 30, "final": 0.025},
    "LUK%": {"value": 12, "final": 0.163},
    "%미반영 LUK": {"value": 200, "final": 0.091},
    "올스탯%": {"value": 9, "final": 1.057},
}


def eff(stat):
    data = EFF_TABLE[stat]
    return data["final"] / data["value"]


# =========================================================
# 아이템 클래스
# =========================================================

class Item:
    def __init__(
        self,
        name,
        price,
        flame_int,
        flame_all,
        scroll_int,
        scroll_magic,
        potential_int,
        additional_int,
        additional_magic,
        used_count,
        max_count=10,
        tax=False
    ):
        self.name = name
        self.price = price

        self.flame_int = flame_int
        self.flame_all = flame_all

        self.scroll_int = scroll_int
        self.scroll_magic = scroll_magic

        self.potential_int = potential_int

        self.additional_int = additional_int
        self.additional_magic = additional_magic

        self.used_count = used_count
        self.max_count = max_count

        # 관세 여부
        self.tax = tax

    @property
    def remaining_count(self):
        return self.max_count - self.used_count

    @property
    def actual_price(self):
        """
        실제 구매가격.
        관세 체크 시 판매가 + 10%
        """
        if self.tax:
            return self.price * 1.10
        return self.price


# =========================================================
# 계산기
# =========================================================

class Calculator:

    @staticmethod
    def final_damage(item):
        result = 0.0

        # 추옵
        result += item.flame_int * eff("INT")
        result += item.flame_all * eff("올스탯%")

        # 작
        result += item.scroll_int * eff("INT")
        result += item.scroll_magic * eff("마력")

        # 잠재
        result += item.potential_int * eff("INT%")

        # 에디
        result += item.additional_int * eff("INT%")
        result += item.additional_magic * eff("마력")

        return result

    @staticmethod
    def damage_difference(item, base):
        return (
            Calculator.final_damage(item)
            - Calculator.final_damage(base)
        )

    @staticmethod
    def price_difference(item, base):
        """
        판매가가 아니라 실제 구매가격 기준.
        """
        return item.actual_price - base.actual_price

    @staticmethod
    def efficiency(item, base):
        damage = Calculator.damage_difference(item, base)
        price = Calculator.price_difference(item, base)

        # 가격 동일
        if price == 0:
            if damage > 0:
                return float("inf")
            return 0.0

        # 더 비싼 매물
        if price > 0:
            if damage <= 0:
                return 0.0

            return damage / price

        # 더 싼 매물
        if damage >= 0:
            return float("inf")

        return damage / abs(price)

    @staticmethod
    def ranking_score(item, base):
        efficiency = Calculator.efficiency(item, base)

        if efficiency == float("inf"):
            return 999999999

        return efficiency


# =========================================================
# GUI
# =========================================================

class AuctionCalculator:

    def __init__(self, root):

        self.root = root

        self.root.title("메이플 경매장 장비 가성비 계산기")
        self.root.geometry("1550x850")
        self.root.minsize(1250, 700)

        self.base_item = None
        self.items = []

        self.base_entries = {}
        self.item_entries = {}

        self.create_ui()

    # =====================================================
    # 전체 UI
    # =====================================================

    def create_ui(self):

        # -------------------------------------------------
        # 제목
        # -------------------------------------------------

        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill="x", padx=15, pady=(12, 5))

        ttk.Label(
            title_frame,
            text="메이플 경매장 장비 가성비 계산기",
            font=("맑은 고딕", 18, "bold")
        ).pack(side="left")

        ttk.Label(
            title_frame,
            text="※ 가성비 = 최종뎀 상승량 / 추가 실구매가격",
            foreground="gray"
        ).pack(side="right", padx=10)

        # -------------------------------------------------
        # 기준 장비
        # -------------------------------------------------

        base_frame = ttk.LabelFrame(
            self.root,
            text="기준 장비",
            padding=10
        )

        base_frame.pack(
            fill="x",
            padx=15,
            pady=5
        )

        self.create_input_area(
            base_frame,
            self.base_entries,
            include_name=False
        )

        ttk.Button(
            base_frame,
            text="기준 장비 설정",
            command=self.set_base
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            padx=5,
            pady=(8, 0),
            sticky="w"
        )

        self.base_status = ttk.Label(
            base_frame,
            text="기준 장비가 설정되지 않았습니다.",
            foreground="gray"
        )

        self.base_status.grid(
            row=3,
            column=2,
            columnspan=8,
            padx=10,
            pady=(8, 0),
            sticky="w"
        )

        # -------------------------------------------------
        # 매물 입력
        # -------------------------------------------------

        item_frame = ttk.LabelFrame(
            self.root,
            text="경매장 매물 입력",
            padding=10
        )

        item_frame.pack(
            fill="x",
            padx=15,
            pady=5
        )

        self.create_input_area(
            item_frame,
            self.item_entries,
            include_name=True
        )

        button_frame = ttk.Frame(item_frame)

        button_frame.grid(
            row=3,
            column=0,
            columnspan=10,
            sticky="w",
            pady=(8, 0)
        )

        ttk.Button(
            button_frame,
            text="매물 등록",
            command=self.add_item
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="입력 초기화",
            command=self.clear_item_input
        ).pack(side="left", padx=5)

        # Enter 키 등록
        self.root.bind(
            "<Return>",
            self.enter_register
        )

        # -------------------------------------------------
        # 결과창
        # -------------------------------------------------

        result_frame = ttk.LabelFrame(
            self.root,
            text="가성비 비교 결과",
            padding=8
        )

        result_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=8
        )

        columns = (
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
            "diff",
            "price_diff",
            "remaining",
            "efficiency"
        )

        self.tree = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings",
            height=18
        )

        headings = {
            "rank": "순위",
            "name": "매물명",
            "price": "판매가",
            "tax": "관세",
            "actual_price": "실구매가",
            "flame": "추옵",
            "scroll": "작",
            "potential": "잠재",
            "additional": "에디",
            "damage": "환산 최종뎀",
            "diff": "기준 대비",
            "price_diff": "가격차",
            "remaining": "잔여 가횟",
            "efficiency": "가성비"
        }

        widths = {
            "rank": 55,
            "name": 150,
            "price": 85,
            "tax": 60,
            "actual_price": 90,
            "flame": 110,
            "scroll": 110,
            "potential": 90,
            "additional": 120,
            "damage": 100,
            "diff": 100,
            "price_diff": 90,
            "remaining": 75,
            "efficiency": 100
        }

        for col in columns:

            self.tree.heading(
                col,
                text=headings[col]
            )

            self.tree.column(
                col,
                width=widths[col],
                anchor="center"
            )

        scrollbar_y = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar_x = ttk.Scrollbar(
            result_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar_y.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scrollbar_x.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)

        # -------------------------------------------------
        # 하단 버튼
        # -------------------------------------------------

        bottom_frame = ttk.Frame(self.root)

        bottom_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 10)
        )

        ttk.Button(
            bottom_frame,
            text="선택 삭제",
            command=self.delete_selected
        ).pack(side="left", padx=3)

        ttk.Button(
            bottom_frame,
            text="전체 삭제",
            command=self.clear_all
        ).pack(side="left", padx=3)

        ttk.Button(
            bottom_frame,
            text="CSV 저장",
            command=self.export_csv
        ).pack(side="left", padx=3)

        ttk.Button(
            bottom_frame,
            text="효율 테이블 보기",
            command=self.open_eff_table
        ).pack(side="right", padx=3)

    # =====================================================
    # 입력 영역
    # =====================================================

    def create_input_area(
        self,
        parent,
        entries,
        include_name
    ):

        fields = [
            ("가격", "price"),
            ("추옵 INT", "flame_int"),
            ("추옵 올스탯 %", "flame_all"),
            ("작 INT", "scroll_int"),
            ("작 마력", "scroll_magic"),
            ("잠재 INT %", "potential_int"),
            ("에디 INT %", "additional_int"),
            ("에디 마력", "additional_magic"),
            ("사용 가횟", "used_count"),
        ]

        if include_name:
            fields.insert(
                0,
                ("매물명", "name")
            )

        for i, (label, key) in enumerate(fields):

            row = i // 5
            col = (i % 5) * 2

            ttk.Label(
                parent,
                text=label
            ).grid(
                row=row,
                column=col,
                padx=(5, 3),
                pady=3,
                sticky="e"
            )

            entry = ttk.Entry(
                parent,
                width=12
            )

            entry.grid(
                row=row,
                column=col + 1,
                padx=(0, 10),
                pady=3,
                sticky="w"
            )

            entries[key] = entry

        # ---------------------------------------------
        # 관세 체크박스
        # ---------------------------------------------

        tax_var = tk.BooleanVar(
            value=False
        )

        tax_check = ttk.Checkbutton(
            parent,
            text="관세",
            variable=tax_var
        )

        # 가격 입력 옆에 배치
        # 가격은 fields의 첫 번째 항목
        tax_check.grid(
            row=0,
            column=10,
            columnspan=2,
            padx=(0, 10),
            sticky="w"
        )

        entries["tax"] = tax_var

    # =====================================================
    # 숫자 입력
    # =====================================================

    def number(
        self,
        entries,
        key,
        default=0
    ):

        text = entries[key].get().strip()

        if text == "":
            return default

        try:
            return float(text)

        except ValueError:

            raise ValueError(
                f"'{key}'에는 숫자를 입력해주세요."
            )

    # =====================================================
    # Item 생성
    # =====================================================

    def create_item(
        self,
        entries,
        name
    ):

        used_count = int(
            self.number(
                entries,
                "used_count"
            )
        )

        if used_count < 0 or used_count > 10:
            raise ValueError(
                "사용 가횟은 0~10 사이로 입력해주세요."
            )

        return Item(
            name=name,
            price=self.number(
                entries,
                "price"
            ),
            flame_int=self.number(
                entries,
                "flame_int"
            ),
            flame_all=self.number(
                entries,
                "flame_all"
            ),
            scroll_int=self.number(
                entries,
                "scroll_int"
            ),
            scroll_magic=self.number(
                entries,
                "scroll_magic"
            ),
            potential_int=self.number(
                entries,
                "potential_int"
            ),
            additional_int=self.number(
                entries,
                "additional_int"
            ),
            additional_magic=self.number(
                entries,
                "additional_magic"
            ),
            used_count=used_count,
            max_count=10,
            tax=entries["tax"].get()
        )

    # =====================================================
    # 기준 장비 설정
    # =====================================================

    def set_base(self):

        try:

            base = self.create_item(
                self.base_entries,
                "기준 장비"
            )

            self.base_item = base

            tax_text = "관세 적용" if base.tax else "관세 없음"

            self.base_status.config(
                text=(
                    f"기준 장비 설정 완료 | "
                    f"판매가 {base.price:.1f}억 | "
                    f"실구매가 {base.actual_price:.1f}억 | "
                    f"{tax_text}"
                ),
                foreground="black"
            )

            self.refresh()

        except ValueError as e:

            messagebox.showerror(
                "입력 오류",
                str(e)
            )

    # =====================================================
    # 매물 등록
    # =====================================================

    def add_item(self):

        try:

            name = self.item_entries["name"].get().strip()

            if not name:
                name = f"매물 {len(self.items) + 1}"

            item = self.create_item(
                self.item_entries,
                name
            )

            self.items.append(item)

            self.refresh()
            self.clear_item_input()

        except ValueError as e:

            messagebox.showerror(
                "입력 오류",
                str(e)
            )

    # =====================================================
    # Enter 등록
    # =====================================================

    def enter_register(self, event=None):

        # 기준 장비 입력창에서 Enter는 등록하지 않음
        focused = self.root.focus_get()

        if focused in self.base_entries.values():
            return

        self.add_item()

    # =====================================================
    # 입력 초기화
    # =====================================================

    def clear_item_input(self):

        for key, entry in self.item_entries.items():

            if key == "tax":
                entry.set(False)
                continue

            entry.delete(
                0,
                tk.END
            )

        # 자주 쓰는 기본값
        self.item_entries["used_count"].insert(
            0,
            "0"
        )

    # =====================================================
    # 결과 갱신
    # =====================================================

    def refresh(self):

        # 기존 결과 삭제
        for row in self.tree.get_children():
            self.tree.delete(row)

        if self.base_item is None:
            return

        # 가성비 계산
        ranked_items = []

        for item in self.items:

            score = Calculator.ranking_score(
                item,
                self.base_item
            )

            ranked_items.append(
                (score, item)
            )

        # 높은 가성비 순
        ranked_items.sort(
            key=lambda x: x[0],
            reverse=True
        )

        # 결과 표시
        for rank, (score, item) in enumerate(
            ranked_items,
            start=1
        ):

            final_damage = Calculator.final_damage(item)

            damage_diff = Calculator.damage_difference(
                item,
                self.base_item
            )

            price_diff = Calculator.price_difference(
                item,
                self.base_item
            )

            # -------------------------
            # 추옵 표시
            # -------------------------

            flame_text = (
                f"INT {item.flame_int:g} / "
                f"올 {item.flame_all:g}%"
            )

            # -------------------------
            # 작 표시
            # -------------------------

            scroll_text = (
                f"INT {item.scroll_int:g} / "
                f"마력 {item.scroll_magic:g}"
            )

            # -------------------------
            # 잠재
            # -------------------------

            potential_text = (
                f"INT {item.potential_int:g}%"
            )

            # -------------------------
            # 에디
            # -------------------------

            additional_text = (
                f"INT {item.additional_int:g}% / "
                f"마력 {item.additional_magic:g}"
            )

            # -------------------------
            # 관세
            # -------------------------

            tax_text = "O" if item.tax else "-"

            # -------------------------
            # 가성비
            # -------------------------

            if score == float("inf"):
                efficiency_text = "∞"
            else:
                efficiency_text = (
                    f"{score:.4f}"
                )

            # -------------------------
            # 가격차
            # -------------------------

            if price_diff > 0:
                price_diff_text = (
                    f"+{price_diff:.1f}"
                )

            elif price_diff < 0:
                price_diff_text = (
                    f"{price_diff:.1f}"
                )

            else:
                price_diff_text = "0.0"

            self.tree.insert(
                "",
                "end",
                values=(
                    rank,
                    item.name,
                    f"{item.price:.1f}",
                    tax_text,
                    f"{item.actual_price:.1f}",
                    flame_text,
                    scroll_text,
                    potential_text,
                    additional_text,
                    f"{final_damage:.3f}%",
                    f"{damage_diff:+.3f}%",
                    price_diff_text,
                    f"{item.remaining_count}/10",
                    efficiency_text
                )
            )

    # =====================================================
    # 선택 삭제
    # =====================================================

    def delete_selected(self):

        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "알림",
                "삭제할 매물을 선택해주세요."
            )
            return

        # Treeview는 정렬된 상태이므로
        # 이름으로 찾아 삭제
        names = []

        for item_id in selected:

            values = self.tree.item(
                item_id,
                "values"
            )

            names.append(
                values[1]
            )

        self.items = [
            item
            for item in self.items
            if item.name not in names
        ]

        self.refresh()

    # =====================================================
    # 전체 삭제
    # =====================================================

    def clear_all(self):

        if not self.items:
            return

        answer = messagebox.askyesno(
            "전체 삭제",
            "등록된 모든 매물을 삭제하시겠습니까?"
        )

        if not answer:
            return

        self.items.clear()

        self.refresh()

    # =====================================================
    # CSV 저장
    # =====================================================

    def export_csv(self):

        if not self.items:
            messagebox.showinfo(
                "알림",
                "저장할 매물이 없습니다."
            )
            return

        filepath = filedialog.asksaveasfilename(
            title="CSV 저장",
            defaultextension=".csv",
            filetypes=[
                ("CSV 파일", "*.csv"),
                ("모든 파일", "*.*")
            ]
        )

        if not filepath:
            return

        try:

            with open(
                filepath,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as f:

                writer = csv.writer(f)

                writer.writerow([
                    "순위",
                    "매물명",
                    "판매가",
                    "관세",
                    "실구매가",
                    "추옵 INT",
                    "추옵 올스탯%",
                    "작 INT",
                    "작 마력",
                    "잠재 INT%",
                    "에디 INT%",
                    "에디 마력",
                    "최종뎀",
                    "기준 대비 최종뎀",
                    "기준 대비 가격",
                    "사용 가횟",
                    "잔여 가횟",
                    "가성비"
                ])

                if self.base_item is None:

                    ranked_items = [
                        (0, item)
                        for item in self.items
                    ]

                else:

                    ranked_items = [
                        (
                            Calculator.ranking_score(
                                item,
                                self.base_item
                            ),
                            item
                        )
                        for item in self.items
                    ]

                    ranked_items.sort(
                        key=lambda x: x[0],
                        reverse=True
                    )

                for rank, (score, item) in enumerate(
                    ranked_items,
                    start=1
                ):

                    if self.base_item:

                        damage = Calculator.final_damage(
                            item
                        )

                        damage_diff = Calculator.damage_difference(
                            item,
                            self.base_item
                        )

                        price_diff = Calculator.price_difference(
                            item,
                            self.base_item
                        )

                    else:

                        damage = Calculator.final_damage(
                            item
                        )

                        damage_diff = 0
                        price_diff = 0

                    if score == float("inf"):
                        efficiency = "∞"
                    else:
                        efficiency = f"{score:.6f}"

                    writer.writerow([
                        rank,
                        item.name,
                        item.price,
                        "O" if item.tax else "X",
                        item.actual_price,
                        item.flame_int,
                        item.flame_all,
                        item.scroll_int,
                        item.scroll_magic,
                        item.potential_int,
                        item.additional_int,
                        item.additional_magic,
                        damage,
                        damage_diff,
                        price_diff,
                        item.used_count,
                        item.remaining_count,
                        efficiency
                    ])

            messagebox.showinfo(
                "저장 완료",
                f"CSV 파일이 저장되었습니다.\n\n{filepath}"
            )

        except Exception as e:

            messagebox.showerror(
                "저장 오류",
                str(e)
            )

    # =====================================================
    # 효율 테이블
    # =====================================================

    def open_eff_table(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "최종뎀 효율 테이블"
        )

        window.geometry(
            "550x500"
        )

        columns = (
            "stat",
            "value",
            "final",
            "per_unit"
        )

        tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings"
        )

        tree.heading(
            "stat",
            text="스탯"
        )

        tree.heading(
            "value",
            text="기준 수치"
        )

        tree.heading(
            "final",
            text="최종뎀"
        )

        tree.heading(
            "per_unit",
            text="1당 효율"
        )

        tree.column(
            "stat",
            width=150,
            anchor="center"
        )

        tree.column(
            "value",
            width=100,
            anchor="center"
        )

        tree.column(
            "final",
            width=100,
            anchor="center"
        )

        tree.column(
            "per_unit",
            width=120,
            anchor="center"
        )

        for stat, data in EFF_TABLE.items():

            per_unit = (
                data["final"]
                / data["value"]
            )

            tree.insert(
                "",
                "end",
                values=(
                    stat,
                    data["value"],
                    f"{data['final']:.3f}%",
                    f"{per_unit:.6f}"
                )
            )

        tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )


# =========================================================
# 실행
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = AuctionCalculator(
        root
    )

    root.mainloop()