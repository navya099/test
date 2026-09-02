# gui/item_panel.py

import tkinter as tk
from tkinter import ttk, messagebox

from models import Item


class ItemPanel(ttk.LabelFrame):

    def __init__(
        self,
        parent,
        on_base_set,
        on_item_add
    ):
        super().__init__(
            parent,
            text="아이템 입력"
        )

        self.on_base_set = on_base_set
        self.on_item_add = on_item_add

        self.entries = {}

        self._build_ui()

    # ========================================================
    # Entry 생성
    # ========================================================

    def _entry(
        self,
        parent,
        label,
        row,
        column,
        default=""
    ):

        ttk.Label(
            parent,
            text=label
        ).grid(
            row=row,
            column=column,
            padx=4,
            pady=3,
            sticky="e"
        )

        entry = ttk.Entry(
            parent,
            width=10
        )

        entry.grid(
            row=row,
            column=column + 1,
            padx=4,
            pady=3
        )

        if default != "":
            entry.insert(0, str(default))

        self.entries[label] = entry

        return entry

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        container = ttk.Frame(self)
        container.pack(
            fill="x",
            padx=10,
            pady=8
        )

        # ----------------------------------------------------
        # 이름 / 가격
        # ----------------------------------------------------

        self._entry(
            container,
            "이름",
            0,
            0
        )

        self._entry(
            container,
            "판매가",
            0,
            2
        )

        self.tax_var = tk.BooleanVar(
            value=False
        )

        ttk.Checkbutton(
            container,
            text="관세 +10%",
            variable=self.tax_var
        ).grid(
            row=0,
            column=4,
            columnspan=2,
            padx=5
        )

        # ----------------------------------------------------
        # 추옵
        # ----------------------------------------------------

        self._entry(
            container,
            "추옵 INT",
            1,
            0
        )

        self._entry(
            container,
            "추옵 올스탯%",
            1,
            2
        )

        # ----------------------------------------------------
        # 작
        # ----------------------------------------------------

        self._entry(
            container,
            "작 INT",
            2,
            0
        )

        self._entry(
            container,
            "작 마력",
            2,
            2
        )

        # ----------------------------------------------------
        # 잠재
        # ----------------------------------------------------

        self._entry(
            container,
            "잠재 INT%",
            3,
            0
        )

        # ----------------------------------------------------
        # 에디
        # ----------------------------------------------------

        self._entry(
            container,
            "에디 INT%",
            3,
            2
        )

        self._entry(
            container,
            "에디 마력",
            3,
            4
        )

        # ----------------------------------------------------
        # 가횟
        # ----------------------------------------------------

        self._entry(
            container,
            "사용 가횟",
            4,
            0,
            0
        )

        # ----------------------------------------------------
        # 버튼
        # ----------------------------------------------------

        button_frame = ttk.Frame(container)
        button_frame.grid(
            row=5,
            column=0,
            columnspan=6,
            pady=8
        )

        ttk.Button(
            button_frame,
            text="기준 아이템 설정",
            command=self._set_base
        ).pack(
            side="left",
            padx=4
        )

        ttk.Button(
            button_frame,
            text="경매장 매물 추가",
            command=self._add_item
        ).pack(
            side="left",
            padx=4
        )

    # ========================================================
    # Item 생성
    # ========================================================

    def _make_item(self):

        try:

            def get_float(label):
                text = self.entries[label].get().strip()

                if text == "":
                    return 0.0

                return float(text)

            def get_int(label):
                text = self.entries[label].get().strip()

                if text == "":
                    return 0

                return int(text)

            return Item(
                name=self.entries["이름"].get().strip(),

                price=get_float("판매가"),

                flame_int=get_float("추옵 INT"),
                flame_all=get_float("추옵 올스탯%"),

                scroll_int=get_float("작 INT"),
                scroll_magic=get_float("작 마력"),

                potential_int=get_float("잠재 INT%"),

                additional_int=get_float("에디 INT%"),
                additional_magic=get_float("에디 마력"),

                used_count=get_int("사용 가횟"),
                max_count=10,

                tax=self.tax_var.get()
            )

        except ValueError:

            messagebox.showerror(
                "입력 오류",
                "숫자 입력란을 확인해주세요.",
                parent=self
            )

            return None

    # ========================================================
    # 기준템
    # ========================================================

    def _set_base(self):

        item = self._make_item()

        if item is None:
            return

        if not item.name:
            messagebox.showwarning(
                "입력 오류",
                "아이템 이름을 입력해주세요.",
                parent=self
            )
            return

        self.on_base_set(item)

    # ========================================================
    # 매물
    # ========================================================

    def _add_item(self):

        item = self._make_item()

        if item is None:
            return

        if not item.name:
            messagebox.showwarning(
                "입력 오류",
                "아이템 이름을 입력해주세요.",
                parent=self
            )
            return

        self.on_item_add(item)

    # ========================================================
    # 초기화
    # ========================================================

    def clear(self):

        for entry in self.entries.values():
            entry.delete(0, tk.END)

        self.entries["사용 가횟"].insert(
            0,
            "0"
        )

        self.tax_var.set(False)