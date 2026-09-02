import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import math


# ============================================================
# 효율 테이블
# ============================================================

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


# ============================================================
# Item
# ============================================================

class Item:

    def __init__(
        self,
        name="",
        price=0.0,

        flame_int=0.0,
        flame_all=0.0,

        scroll_int=0.0,
        scroll_magic=0.0,

        potential_int=0.0,

        additional_int=0.0,
        additional_magic=0.0,

        used_count=0,
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

        self.tax = tax

    # --------------------------------------------------------
    # 남은 가횟
    # --------------------------------------------------------

    @property
    def remaining_count(self):
        return self.max_count - self.used_count

    # --------------------------------------------------------
    # 실제 구매가
    # --------------------------------------------------------

    @property
    def actual_price(self):
        if self.tax:
            return self.price * 1.10

        return self.price

    # --------------------------------------------------------
    # JSON 저장용
    # --------------------------------------------------------

    def to_dict(self):

        return {
            "name": self.name,
            "price": self.price,
            "tax": self.tax,

            "flame_int": self.flame_int,
            "flame_all": self.flame_all,

            "scroll_int": self.scroll_int,
            "scroll_magic": self.scroll_magic,

            "potential_int": self.potential_int,

            "additional_int": self.additional_int,
            "additional_magic": self.additional_magic,

            "used_count": self.used_count,
            "max_count": self.max_count
        }

    # --------------------------------------------------------
    # JSON 불러오기
    # --------------------------------------------------------

    @classmethod
    def from_dict(cls, data):

        return cls(
            name=data.get("name", ""),
            price=data.get("price", 0.0),

            flame_int=data.get("flame_int", 0.0),
            flame_all=data.get("flame_all", 0.0),

            scroll_int=data.get("scroll_int", 0.0),
            scroll_magic=data.get("scroll_magic", 0.0),

            potential_int=data.get("potential_int", 0.0),

            additional_int=data.get("additional_int", 0.0),
            additional_magic=data.get("additional_magic", 0.0),

            used_count=data.get("used_count", 0),
            max_count=data.get("max_count", 10),

            tax=data.get("tax", False)
        )


# ============================================================
# Equipment
# ============================================================

class Equipment:

    def __init__(self, name):

        self.name = name

        # 기준 아이템
        self.base_item = Item()

        # 경매장 매물
        self.items = []

    # --------------------------------------------------------
    # 기준템 설정
    # --------------------------------------------------------

    def set_base(self, item):

        self.base_item = item

    # --------------------------------------------------------
    # 매물 추가
    # --------------------------------------------------------

    def add_item(self, item):

        self.items.append(item)

    # --------------------------------------------------------
    # 이름으로 매물 삭제
    # --------------------------------------------------------

    def remove_item_by_name(self, name):

        self.items = [
            item for item in self.items
            if item.name != name
        ]

    # --------------------------------------------------------
    # 전체 매물 삭제
    # --------------------------------------------------------

    def clear_items(self):

        self.items.clear()

    # --------------------------------------------------------
    # JSON 저장
    # --------------------------------------------------------

    def to_dict(self):

        return {
            "base_item": self.base_item.to_dict(),

            "items": [
                item.to_dict()
                for item in self.items
            ]
        }

    # --------------------------------------------------------
    # JSON 불러오기
    # --------------------------------------------------------

    @classmethod
    def from_dict(cls, name, data):

        equipment = cls(name)

        base_data = data.get("base_item")

        if base_data:
            equipment.base_item = Item.from_dict(base_data)

        equipment.items = [
            Item.from_dict(item_data)
            for item_data in data.get("items", [])
        ]

        return equipment


# ============================================================
# EquipmentManager
# ============================================================

class EquipmentManager:

    SAVE_VERSION = 1

    DEFAULT_EQUIPMENTS = [
        "귀고리",
        "펜던트",
        "반지",
        "눈장",
        "얼장",
        "견장",
        "망토",
        "모자",
        "상의",
        "하의",
        "장갑",
        "신발",
        "무기"
    ]

    def __init__(self):

        self.equipments = {}

        for name in self.DEFAULT_EQUIPMENTS:
            self.add_equipment(name)

    # --------------------------------------------------------
    # 장비 추가
    # --------------------------------------------------------

    def add_equipment(self, name):

        if name not in self.equipments:
            self.equipments[name] = Equipment(name)

    # --------------------------------------------------------
    # 장비 삭제
    # --------------------------------------------------------

    def remove_equipment(self, name):

        if name in self.equipments:
            del self.equipments[name]

    # --------------------------------------------------------
    # 장비 가져오기
    # --------------------------------------------------------

    def get_equipment(self, name):

        return self.equipments.get(name)

    # --------------------------------------------------------
    # 장비 이름 목록
    # --------------------------------------------------------

    def get_names(self):

        return list(self.equipments.keys())

    # ========================================================
    # JSON 저장
    # ========================================================

    def save(self, filepath):

        data = {
            "version": self.SAVE_VERSION,
            "app": "MapleAuctionCalculator",

            "equipments": {
                name: equipment.to_dict()
                for name, equipment in self.equipments.items()
            }
        }

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

    # ========================================================
    # JSON 로드
    # ========================================================

    def load(self, filepath):

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        version = data.get("version", 1)

        if version != self.SAVE_VERSION:

            raise ValueError(
                f"지원하지 않는 저장 파일 버전입니다.\n"
                f"파일 버전: {version}\n"
                f"현재 버전: {self.SAVE_VERSION}"
            )

        equipments_data = data.get("equipments", {})

        self.equipments = {}

        for name, equipment_data in equipments_data.items():

            self.equipments[name] = Equipment.from_dict(
                name,
                equipment_data
            )


# ============================================================
# Calculator
# ============================================================

class Calculator:

    @staticmethod
    def efficiency(stat_name):

        return (
            EFF_TABLE[stat_name]["final"]
            / EFF_TABLE[stat_name]["value"]
        )

    # --------------------------------------------------------
    # 최종뎀 계산
    # --------------------------------------------------------

    @classmethod
    def final_damage(cls, item):

        damage = 0

        # 추옵
        damage += (
            item.flame_int
            * cls.efficiency("INT")
        )

        damage += (
            item.flame_all
            * cls.efficiency("올스탯%")
        )

        # 작
        damage += (
            item.scroll_int
            * cls.efficiency("INT")
        )

        damage += (
            item.scroll_magic
            * cls.efficiency("마력")
        )

        # 잠재
        damage += (
            item.potential_int
            * cls.efficiency("INT%")
        )

        # 에디
        damage += (
            item.additional_int
            * cls.efficiency("INT%")
        )

        damage += (
            item.additional_magic
            * cls.efficiency("마력")
        )

        return damage

    # --------------------------------------------------------
    # 기준템 대비 최종뎀
    # --------------------------------------------------------

    @classmethod
    def damage_difference(cls, item, base):

        return (
            cls.final_damage(item)
            - cls.final_damage(base)
        )

    # --------------------------------------------------------
    # 가격 차이
    # --------------------------------------------------------

    @staticmethod
    def price_difference(item, base):

        return (
            item.actual_price
            - base.actual_price
        )

    # --------------------------------------------------------
    # 가성비
    # --------------------------------------------------------

    @classmethod
    def efficiency_score(cls, item, base):

        damage_diff = cls.damage_difference(
            item,
            base
        )

        price_diff = cls.price_difference(
            item,
            base
        )

        # 가격 동일 + 성능 상승
        if price_diff == 0:

            if damage_diff > 0:
                return math.inf

            return 0

        # 더 비싼데 성능이 같거나 낮음
        if price_diff > 0:

            if damage_diff <= 0:
                return 0

            return (
                damage_diff
                / price_diff
            )

        # 더 싼데 성능이 같거나 좋음
        if damage_diff >= 0:
            return math.inf

        # 더 싼 대신 성능 하락
        return (
            damage_diff
            / abs(price_diff)
        )

    # --------------------------------------------------------
    # 정렬용 점수
    # --------------------------------------------------------

    @classmethod
    def ranking_score(cls, item, base):

        value = cls.efficiency_score(
            item,
            base
        )

        if math.isinf(value):
            return 999999999

        return value


# ============================================================
# GUI
# ============================================================

class AuctionCalculator:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "메이플 경매장 장비 가성비 계산기"
        )

        self.root.geometry(
            "1450x850"
        )

        # ----------------------------------------------------
        # 데이터
        # ----------------------------------------------------

        self.manager = EquipmentManager()

        self.current_equipment_name = (
            self.manager.get_names()[0]
        )

        # ----------------------------------------------------
        # 상단
        # ----------------------------------------------------

        title_frame = ttk.Frame(root)

        title_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        ttk.Label(
            title_frame,
            text="메이플 경매장 장비 가성비 계산기",
            font=("맑은 고딕", 18, "bold")
        ).pack(side="left")

        # ----------------------------------------------------
        # 저장 / 로드
        # ----------------------------------------------------

        ttk.Button(
            title_frame,
            text="💾 전체 저장",
            command=self.save_all
        ).pack(
            side="right",
            padx=3
        )

        ttk.Button(
            title_frame,
            text="📂 전체 불러오기",
            command=self.load_all
        ).pack(
            side="right",
            padx=3
        )

        # ----------------------------------------------------
        # 장비 선택
        # ----------------------------------------------------

        equipment_frame = ttk.LabelFrame(
            root,
            text="장비 선택"
        )

        equipment_frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        self.equipment_buttons_frame = ttk.Frame(
            equipment_frame
        )

        self.equipment_buttons_frame.pack(
            side="left",
            fill="x",
            expand=True
        )

        ttk.Button(
            equipment_frame,
            text="+ 장비 추가",
            command=self.add_equipment
        ).pack(
            side="right",
            padx=5
        )

        ttk.Button(
            equipment_frame,
            text="현재 장비 삭제",
            command=self.delete_equipment
        ).pack(
            side="right",
            padx=5
        )

        self.refresh_equipment_buttons()

        # ----------------------------------------------------
        # 현재 장비 표시
        # ----------------------------------------------------

        self.current_label = ttk.Label(
            root,
            text="",
            font=("맑은 고딕", 13, "bold")
        )

        self.current_label.pack(
            anchor="w",
            padx=15,
            pady=5
        )

        # ----------------------------------------------------
        # 입력 영역
        # ----------------------------------------------------

        input_frame = ttk.Frame(root)

        input_frame.pack(
            fill="x",
            padx=10,
            pady=5
        )

        # ====================================================
        # 기준 아이템
        # ====================================================

        base_frame = ttk.LabelFrame(
            input_frame,
            text="기준 아이템"
        )

        base_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 5)
        )

        self.base_vars = self.create_item_inputs(
            base_frame
        )

        ttk.Button(
            base_frame,
            text="기준템 적용",
            command=self.apply_base
        ).grid(
            row=10,
            column=0,
            columnspan=4,
            pady=8
        )

        # ====================================================
        # 경매장 매물
        # ====================================================

        item_frame = ttk.LabelFrame(
            input_frame,
            text="경매장 매물"
        )

        item_frame.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(5, 0)
        )

        self.item_vars = self.create_item_inputs(
            item_frame,
            include_name=True
        )

        ttk.Button(
            item_frame,
            text="매물 추가",
            command=self.add_item
        ).grid(
            row=10,
            column=0,
            columnspan=4,
            pady=8
        )

        # ----------------------------------------------------
        # 결과
        # ----------------------------------------------------

        result_frame = ttk.LabelFrame(
            root,
            text="경매장 매물 비교"
        )

        result_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        columns = (
            "rank",
            "name",
            "sale_price",
            "tax",
            "actual_price",
            "flame",
            "scroll",
            "potential",
            "additional",
            "damage",
            "difference",
            "price_diff",
            "count",
            "efficiency"
        )

        self.tree = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "rank": "순위",
            "name": "이름",
            "sale_price": "판매가",
            "tax": "관세",
            "actual_price": "실구매가",
            "flame": "추옵",
            "scroll": "작",
            "potential": "잠재",
            "additional": "에디",
            "damage": "환산 최종뎀",
            "difference": "기준 대비",
            "price_diff": "가격차",
            "count": "잔여 가횟",
            "efficiency": "가성비"
        }

        widths = {
            "rank": 50,
            "name": 150,
            "sale_price": 80,
            "tax": 60,
            "actual_price": 90,
            "flame": 150,
            "scroll": 120,
            "potential": 100,
            "additional": 120,
            "damage": 110,
            "difference": 100,
            "price_diff": 90,
            "count": 80,
            "efficiency": 100
        }

        for column in columns:

            self.tree.heading(
                column,
                text=headings[column]
            )

            self.tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # ----------------------------------------------------
        # 하단 버튼
        # ----------------------------------------------------

        bottom_frame = ttk.Frame(root)

        bottom_frame.pack(
            fill="x",
            padx=10,
            pady=8
        )

        ttk.Button(
            bottom_frame,
            text="선택 매물 삭제",
            command=self.delete_selected
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            bottom_frame,
            text="현재 장비 매물 전체 삭제",
            command=self.clear_items
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            bottom_frame,
            text="현재 장비 CSV 저장",
            command=self.export_csv
        ).pack(
            side="right",
            padx=3
        )

        # ----------------------------------------------------
        # 초기화
        # ----------------------------------------------------

        self.refresh_ui()

    # ========================================================
    # 입력창 생성
    # ========================================================

    def create_item_inputs(
        self,
        parent,
        include_name=False
    ):

        vars = {}

        row = 0

        if include_name:

            ttk.Label(
                parent,
                text="이름"
            ).grid(
                row=row,
                column=0,
                padx=5,
                pady=3
            )

            vars["name"] = tk.StringVar()

            ttk.Entry(
                parent,
                textvariable=vars["name"],
                width=25
            ).grid(
                row=row,
                column=1,
                columnspan=3,
                padx=5,
                pady=3
            )

            row += 1

        fields = [
            ("price", "판매가"),
            ("flame_int", "추옵 INT"),
            ("flame_all", "추옵 올스탯%"),
            ("scroll_int", "작 INT"),
            ("scroll_magic", "작 마력"),
            ("potential_int", "잠재 INT%"),
            ("additional_int", "에디 INT%"),
            ("additional_magic", "에디 마력"),
            ("used_count", "사용 가횟"),
        ]

        for key, label in fields:

            ttk.Label(
                parent,
                text=label
            ).grid(
                row=row,
                column=0,
                padx=5,
                pady=3
            )

            var = tk.StringVar()

            vars[key] = var

            ttk.Entry(
                parent,
                textvariable=var,
                width=15
            ).grid(
                row=row,
                column=1,
                padx=5,
                pady=3
            )

            row += 1

        vars["tax"] = tk.BooleanVar()

        ttk.Checkbutton(
            parent,
            text="관세 +10%",
            variable=vars["tax"]
        ).grid(
            row=0,
            column=2,
            columnspan=2,
            padx=5,
            pady=3
        )

        return vars

    # ========================================================
    # 숫자 가져오기
    # ========================================================

    @staticmethod
    def get_float(var):

        value = var.get().strip()

        if value == "":
            return 0.0

        return float(value)

    # ========================================================
    # Item 생성
    # ========================================================

    def make_item(
        self,
        vars,
        include_name=False
    ):

        name = ""

        if include_name:

            name = vars["name"].get().strip()

        return Item(

            name=name,

            price=self.get_float(
                vars["price"]
            ),

            flame_int=self.get_float(
                vars["flame_int"]
            ),

            flame_all=self.get_float(
                vars["flame_all"]
            ),

            scroll_int=self.get_float(
                vars["scroll_int"]
            ),

            scroll_magic=self.get_float(
                vars["scroll_magic"]
            ),

            potential_int=self.get_float(
                vars["potential_int"]
            ),

            additional_int=self.get_float(
                vars["additional_int"]
            ),

            additional_magic=self.get_float(
                vars["additional_magic"]
            ),

            used_count=int(
                self.get_float(
                    vars["used_count"]
                )
            ),

            tax=vars["tax"].get()
        )

    # ========================================================
    # 현재 장비
    # ========================================================

    @property
    def current_equipment(self):

        return self.manager.get_equipment(
            self.current_equipment_name
        )

    # ========================================================
    # 장비 버튼 갱신
    # ========================================================

    def refresh_equipment_buttons(self):

        for widget in self.equipment_buttons_frame.winfo_children():

            widget.destroy()

        for name in self.manager.get_names():

            button = ttk.Button(
                self.equipment_buttons_frame,
                text=name,
                command=lambda n=name:
                    self.select_equipment(n)
            )

            button.pack(
                side="left",
                padx=2
            )

    # ========================================================
    # 장비 선택
    # ========================================================

    def select_equipment(self, name):

        self.current_equipment_name = name

        self.refresh_ui()

    # ========================================================
    # UI 갱신
    # ========================================================

    def refresh_ui(self):

        self.current_label.config(
            text=f"현재 장비 : {self.current_equipment_name}"
        )

        equipment = self.current_equipment

        # ----------------------------------------------------
        # 기준템 표시
        # ----------------------------------------------------

        base = equipment.base_item

        self.base_vars["price"].set(
            self.number_text(base.price)
        )

        self.base_vars["flame_int"].set(
            self.number_text(base.flame_int)
        )

        self.base_vars["flame_all"].set(
            self.number_text(base.flame_all)
        )

        self.base_vars["scroll_int"].set(
            self.number_text(base.scroll_int)
        )

        self.base_vars["scroll_magic"].set(
            self.number_text(base.scroll_magic)
        )

        self.base_vars["potential_int"].set(
            self.number_text(base.potential_int)
        )

        self.base_vars["additional_int"].set(
            self.number_text(base.additional_int)
        )

        self.base_vars["additional_magic"].set(
            self.number_text(base.additional_magic)
        )

        self.base_vars["used_count"].set(
            self.number_text(base.used_count)
        )

        self.base_vars["tax"].set(
            base.tax
        )

        self.refresh_results()

    # ========================================================
    # 숫자 표시
    # ========================================================

    @staticmethod
    def number_text(value):

        if value == 0:
            return ""

        if float(value).is_integer():

            return str(
                int(value)
            )

        return str(value)

    # ========================================================
    # 기준템 적용
    # ========================================================

    def apply_base(self):

        try:

            item = self.make_item(
                self.base_vars
            )

            self.current_equipment.set_base(
                item
            )

            self.refresh_results()

        except ValueError:

            messagebox.showerror(
                "입력 오류",
                "숫자 입력값을 확인해주세요."
            )

    # ========================================================
    # 매물 추가
    # ========================================================

    def add_item(self):

        try:

            item = self.make_item(
                self.item_vars,
                include_name=True
            )

            if item.name == "":

                messagebox.showwarning(
                    "입력 오류",
                    "매물 이름을 입력해주세요."
                )

                return

            self.current_equipment.add_item(
                item
            )

            self.clear_item_input()

            self.refresh_results()

        except ValueError:

            messagebox.showerror(
                "입력 오류",
                "숫자 입력값을 확인해주세요."
            )

    # ========================================================
    # 매물 입력창 초기화
    # ========================================================

    def clear_item_input(self):

        for key, var in self.item_vars.items():

            if key == "tax":

                var.set(False)

            else:

                var.set("")

    # ========================================================
    # 결과 갱신
    # ========================================================

    def refresh_results(self):

        for row in self.tree.get_children():

            self.tree.delete(row)

        equipment = self.current_equipment

        base = equipment.base_item

        items = list(
            equipment.items
        )

        items.sort(
            key=lambda item:
                Calculator.ranking_score(
                    item,
                    base
                ),
            reverse=True
        )

        for rank, item in enumerate(
            items,
            start=1
        ):

            damage = Calculator.final_damage(
                item
            )

            difference = Calculator.damage_difference(
                item,
                base
            )

            price_difference = Calculator.price_difference(
                item,
                base
            )

            efficiency = Calculator.efficiency_score(
                item,
                base
            )

            # ------------------------------------------------
            # 표시
            # ------------------------------------------------

            flame_text = (
                f"INT {item.flame_int:g} / "
                f"올스탯 {item.flame_all:g}%"
            )

            scroll_text = (
                f"INT {item.scroll_int:g} / "
                f"마력 {item.scroll_magic:g}"
            )

            potential_text = (
                f"INT {item.potential_int:g}%"
            )

            additional_text = (
                f"INT {item.additional_int:g}% / "
                f"마력 {item.additional_magic:g}"
            )

            if math.isinf(efficiency):

                efficiency_text = "∞"

            else:

                efficiency_text = (
                    f"{efficiency:.5f}"
                )

            tax_text = "O" if item.tax else "X"

            self.tree.insert(
                "",
                "end",
                values=(

                    rank,

                    item.name,

                    f"{item.price:.1f}억",

                    tax_text,

                    f"{item.actual_price:.1f}억",

                    flame_text,

                    scroll_text,

                    potential_text,

                    additional_text,

                    f"{damage:.3f}%",

                    f"{difference:+.3f}%",

                    f"{price_difference:+.1f}억",

                    f"{item.remaining_count}/{item.max_count}",

                    efficiency_text
                )
            )

    # ========================================================
    # 선택 매물 삭제
    # ========================================================

    def delete_selected(self):

        selected = self.tree.selection()

        if not selected:
            return

        names = []

        for row_id in selected:

            values = self.tree.item(
                row_id,
                "values"
            )

            names.append(
                values[1]
            )

        self.current_equipment.items = [

            item

            for item in self.current_equipment.items

            if item.name not in names
        ]

        self.refresh_results()

    # ========================================================
    # 현재 장비 매물 전체 삭제
    # ========================================================

    def clear_items(self):

        result = messagebox.askyesno(
            "확인",
            f"[{self.current_equipment_name}] "
            "모든 매물을 삭제하시겠습니까?"
        )

        if not result:
            return

        self.current_equipment.clear_items()

        self.refresh_results()

    # ========================================================
    # 장비 추가
    # ========================================================

    def add_equipment(self):

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "장비 추가"
        )

        dialog.geometry(
            "300x130"
        )

        ttk.Label(
            dialog,
            text="장비 이름"
        ).pack(
            pady=(15, 5)
        )

        name_var = tk.StringVar()

        entry = ttk.Entry(
            dialog,
            textvariable=name_var
        )

        entry.pack()

        entry.focus()

        def confirm():

            name = name_var.get().strip()

            if not name:
                return

            if name in self.manager.equipments:

                messagebox.showwarning(
                    "중복",
                    "이미 존재하는 장비입니다."
                )

                return

            self.manager.add_equipment(
                name
            )

            self.current_equipment_name = name

            self.refresh_equipment_buttons()

            self.refresh_ui()

            dialog.destroy()

        ttk.Button(
            dialog,
            text="추가",
            command=confirm
        ).pack(
            pady=10
        )

    # ========================================================
    # 장비 삭제
    # ========================================================

    def delete_equipment(self):

        if len(self.manager.equipments) <= 1:

            messagebox.showwarning(
                "삭제 불가",
                "최소 하나의 장비는 남아있어야 합니다."
            )

            return

        result = messagebox.askyesno(
            "장비 삭제",
            f"[{self.current_equipment_name}] 장비와 "
            "그 안의 모든 매물을 삭제하시겠습니까?"
        )

        if not result:
            return

        self.manager.remove_equipment(
            self.current_equipment_name
        )

        self.current_equipment_name = (
            self.manager.get_names()[0]
        )

        self.refresh_equipment_buttons()

        self.refresh_ui()

    # ========================================================
    # 전체 저장
    # ========================================================

    def save_all(self):

        filepath = filedialog.asksaveasfilename(

            title="전체 데이터 저장",

            defaultextension=".json",

            filetypes=[
                ("JSON 파일", "*.json"),
                ("모든 파일", "*.*")
            ]
        )

        if not filepath:
            return

        try:

            self.manager.save(
                filepath
            )

            messagebox.showinfo(
                "저장 완료",
                "전체 장비 데이터가 저장되었습니다."
            )

        except Exception as e:

            messagebox.showerror(
                "저장 오류",
                str(e)
            )

    # ========================================================
    # 전체 불러오기
    # ========================================================

    def load_all(self):

        filepath = filedialog.askopenfilename(

            title="전체 데이터 불러오기",

            filetypes=[
                ("JSON 파일", "*.json"),
                ("모든 파일", "*.*")
            ]
        )

        if not filepath:
            return

        result = messagebox.askyesno(
            "데이터 불러오기",
            "현재 데이터가 불러온 데이터로 교체됩니다.\n"
            "계속하시겠습니까?"
        )

        if not result:
            return

        try:

            self.manager.load(
                filepath
            )

            names = self.manager.get_names()

            if not names:

                self.manager.add_equipment(
                    "귀고리"
                )

            self.current_equipment_name = (
                self.manager.get_names()[0]
            )

            self.refresh_equipment_buttons()

            self.refresh_ui()

            messagebox.showinfo(
                "불러오기 완료",
                "전체 장비 데이터가 불러와졌습니다."
            )

        except json.JSONDecodeError:

            messagebox.showerror(
                "불러오기 오류",
                "올바른 JSON 저장 파일이 아닙니다."
            )

        except Exception as e:

            messagebox.showerror(
                "불러오기 오류",
                str(e)
            )

    # ========================================================
    # CSV 저장
    # ========================================================

    def export_csv(self):

        filepath = filedialog.asksaveasfilename(

            title="CSV 저장",

            defaultextension=".csv",

            filetypes=[
                ("CSV 파일", "*.csv")
            ]
        )

        if not filepath:
            return

        equipment = self.current_equipment

        base = equipment.base_item

        items = equipment.items

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
                    "이름",
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

                    "환산 최종뎀",
                    "기준 대비",
                    "가격차",

                    "사용 가횟",
                    "최대 가횟",
                    "잔여 가횟",

                    "가성비"
                ])

                sorted_items = sorted(
                    items,
                    key=lambda item:
                        Calculator.ranking_score(
                            item,
                            base
                        ),
                    reverse=True
                )

                for rank, item in enumerate(
                    sorted_items,
                    start=1
                ):

                    damage = Calculator.final_damage(
                        item
                    )

                    difference = Calculator.damage_difference(
                        item,
                        base
                    )

                    price_difference = Calculator.price_difference(
                        item,
                        base
                    )

                    efficiency = Calculator.efficiency_score(
                        item,
                        base
                    )

                    efficiency_text = (
                        "INF"
                        if math.isinf(efficiency)
                        else f"{efficiency:.6f}"
                    )

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
                        difference,
                        price_difference,

                        item.used_count,
                        item.max_count,
                        item.remaining_count,

                        efficiency_text
                    ])

            messagebox.showinfo(
                "CSV 저장 완료",
                "CSV 파일이 저장되었습니다."
            )

        except Exception as e:

            messagebox.showerror(
                "CSV 저장 오류",
                str(e)
            )


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = AuctionCalculator(
        root
    )

    root.mainloop()