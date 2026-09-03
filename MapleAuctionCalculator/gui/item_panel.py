# gui/item_panel.py

import tkinter as tk
from tkinter import ttk, messagebox

from models.item import Item
from models.option import StatOption

from models.option_datas import (
    SLOTS,
    POTENTIAL_GRADES,
    POTENTIAL_OPTIONS,
    ADDITIONAL_OPTIONS,
    FLAME_PRESETS,
    SCROLL_PRESETS,
)


class ItemPanel(ttk.LabelFrame):

    def __init__(
        self,
        parent,
        on_base_set,
        on_item_add,
        mode="auction",
        on_close=None
    ):
        super().__init__(
            parent,
            text="아이템 입력"
        )

        self.on_base_set = on_base_set
        self.on_item_add = on_item_add
        self.mode = mode
        self.on_close = on_close
        # ====================================================
        # 변수
        # ====================================================

        self.name_var = tk.StringVar()
        self.slot_var = tk.StringVar(
            value=SLOTS[0] if SLOTS else ""
        )

        # UI 전용 아이템 프리셋 번호
        self.item_preset_var = tk.StringVar(
            value="1"
        )

        self.starforce_var = tk.IntVar(
            value=0
        )

        self.price_var = tk.StringVar()
        self.tax_var = tk.BooleanVar(
            value=False
        )

        self.used_count_var = tk.IntVar(
            value=0
        )

        # ====================================================
        # 추옵
        # ====================================================

        self.flame_entries = {}

        self.flame_preset_var = tk.StringVar(
            value=""
        )

        # ====================================================
        # 작
        # ====================================================

        self.scroll_entries = {}

        self.scroll_preset_var = tk.StringVar(
            value=""
        )

        # ====================================================
        # 잠재
        # ====================================================

        self.potential_grade_var = tk.StringVar(
            value="레전드리"
        )

        self.potential_vars = [
            tk.StringVar(value="없음"),
            tk.StringVar(value="없음"),
            tk.StringVar(value="없음"),
        ]

        # ====================================================
        # 에디
        # ====================================================

        self.additional_grade_var = tk.StringVar(
            value="에픽"
        )

        self.additional_vars = [
            tk.StringVar(value="없음"),
            tk.StringVar(value="없음"),
            tk.StringVar(value="없음"),
        ]

        self._build_ui()

    # ========================================================
    # 공통
    # ========================================================

    def _section(self, title):
        """
        섹션 제목 + 내부 Frame 생성.
        """

        frame = ttk.LabelFrame(
            self,
            text=title
        )

        frame.pack(
            fill="x",
            padx=8,
            pady=4
        )

        return frame

    def _label_entry(
        self,
        parent,
        label,
        variable,
        row,
        column,
        width=10
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
            textvariable=variable,
            width=width
        )

        entry.grid(
            row=row,
            column=column + 1,
            padx=4,
            pady=3,
            sticky="w"
        )

        return entry

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        self._build_basic_section()

        self._build_starforce_section()

        self._build_flame_section()

        self._build_scroll_section()

        self._build_potential_section()

        self._build_additional_section()

        self._build_price_section()

        self._build_buttons()

    # ========================================================
    # 장비 정보
    # ========================================================

    def _build_basic_section(self):

        frame = self._section("장비 정보")

        # ----------------------------------------------------
        # 부위
        # ----------------------------------------------------

        ttk.Label(
            frame,
            text="부위"
        ).grid(
            row=0,
            column=0,
            padx=4,
            pady=3,
            sticky="e"
        )

        self.slot_combo = ttk.Combobox(
            frame,
            textvariable=self.slot_var,
            values=SLOTS,
            state="readonly",
            width=14
        )

        self.slot_combo.grid(
            row=0,
            column=1,
            padx=4,
            pady=3,
            sticky="w"
        )

        # ----------------------------------------------------
        # 이름
        # ----------------------------------------------------

        self._label_entry(
            frame,
            "이름",
            self.name_var,
            1,
            0,
            width=20
        )

        # ----------------------------------------------------
        # 프리셋
        # ----------------------------------------------------

        ttk.Label(
            frame,
            text="프리셋"
        ).grid(
            row=2,
            column=0,
            padx=4,
            pady=3,
            sticky="e"
        )

        self.item_preset_combo = ttk.Combobox(
            frame,
            textvariable=self.item_preset_var,
            values=["1", "2", "3", "4", "5"],
            state="readonly",
            width=14
        )

        self.item_preset_combo.grid(
            row=2,
            column=1,
            padx=4,
            pady=3,
            sticky="w"
        )

    # ========================================================
    # 스타포스
    # ========================================================

    def _build_starforce_section(self):

        frame = self._section("스타포스 정보")

        ttk.Label(
            frame,
            text="스타포스"
        ).grid(
            row=0,
            column=0,
            padx=4,
            pady=4,
            sticky="e"
        )

        ttk.Spinbox(
            frame,
            from_=0,
            to=30,
            textvariable=self.starforce_var,
            width=8
        ).grid(
            row=0,
            column=1,
            padx=4,
            pady=4,
            sticky="w"
        )

    # ========================================================
    # 추옵
    # ========================================================

    def _build_flame_section(self):

        frame = self._section("추옵 정보")

        # ----------------------------------------------------
        # 프리셋
        # ----------------------------------------------------

        ttk.Label(
            frame,
            text="프리셋"
        ).grid(
            row=0,
            column=0,
            padx=4,
            pady=3,
            sticky="e"
        )

        preset_names = list(
            FLAME_PRESETS.keys()
        )

        self.flame_preset_combo = ttk.Combobox(
            frame,
            textvariable=self.flame_preset_var,
            values=preset_names,
            state="readonly",
            width=18
        )

        self.flame_preset_combo.grid(
            row=0,
            column=1,
            columnspan=2,
            padx=4,
            pady=3,
            sticky="w"
        )

        self.flame_preset_combo.bind(
            "<<ComboboxSelected>>",
            self._apply_flame_preset
        )

        # ----------------------------------------------------
        # 스탯
        # ----------------------------------------------------

        stats = [
            "STR",
            "DEX",
            "INT",
            "LUK",
            "공격력",
            "마력",
            "올스탯%",
        ]

        for index, stat in enumerate(stats):

            row = 1 + index // 4
            column = (index % 4) * 2

            variable = tk.StringVar(
                value=""
            )

            self.flame_entries[stat] = variable

            ttk.Label(
                frame,
                text=stat
            ).grid(
                row=row,
                column=column,
                padx=3,
                pady=3,
                sticky="e"
            )

            ttk.Entry(
                frame,
                textvariable=variable,
                width=7
            ).grid(
                row=row,
                column=column + 1,
                padx=3,
                pady=3,
                sticky="w"
            )

    # ========================================================
    # 작
    # ========================================================

    def _build_scroll_section(self):

        frame = self._section("작 정보")

        # ----------------------------------------------------
        # 프리셋
        # ----------------------------------------------------

        ttk.Label(
            frame,
            text="프리셋"
        ).grid(
            row=0,
            column=0,
            padx=4,
            pady=3,
            sticky="e"
        )

        preset_names = list(
            SCROLL_PRESETS.keys()
        )

        self.scroll_preset_combo = ttk.Combobox(
            frame,
            textvariable=self.scroll_preset_var,
            values=preset_names,
            state="readonly",
            width=18
        )

        self.scroll_preset_combo.grid(
            row=0,
            column=1,
            columnspan=2,
            padx=4,
            pady=3,
            sticky="w"
        )

        self.scroll_preset_combo.bind(
            "<<ComboboxSelected>>",
            self._apply_scroll_preset
        )

        # ----------------------------------------------------
        # 스탯
        # ----------------------------------------------------

        stats = [
            "STR",
            "DEX",
            "INT",
            "LUK",
            "공격력",
            "마력",
        ]

        for index, stat in enumerate(stats):

            row = 1 + index // 3
            column = (index % 3) * 2

            variable = tk.StringVar(
                value=""
            )

            self.scroll_entries[stat] = variable

            ttk.Label(
                frame,
                text=stat
            ).grid(
                row=row,
                column=column,
                padx=3,
                pady=3,
                sticky="e"
            )

            ttk.Entry(
                frame,
                textvariable=variable,
                width=7
            ).grid(
                row=row,
                column=column + 1,
                padx=3,
                pady=3,
                sticky="w"
            )

    # ========================================================
    # 잠재
    # ========================================================

    def _build_potential_section(self):

        frame = self._section("잠재능력")

        # ----------------------------------------------------
        # 등급
        # ----------------------------------------------------

        ttk.Label(
            frame,
            text="등급"
        ).grid(
            row=0,
            column=0,
            padx=4,
            pady=3,
            sticky="e"
        )

        ttk.Combobox(
            frame,
            textvariable=self.potential_grade_var,
            values=POTENTIAL_GRADES,
            state="readonly",
            width=14
        ).grid(
            row=0,
            column=1,
            padx=4,
            pady=3,
            sticky="w"
        )

        # ----------------------------------------------------
        # 옵션
        # ----------------------------------------------------

        option_values = [
            option[0]
            for option in POTENTIAL_OPTIONS
        ]

        for index, variable in enumerate(
            self.potential_vars
        ):

            ttk.Label(
                frame,
                text=f"{index + 1}."
            ).grid(
                row=index + 1,
                column=0,
                padx=4,
                pady=3,
                sticky="e"
            )

            ttk.Combobox(
                frame,
                textvariable=variable,
                values=option_values,
                state="readonly",
                width=22
            ).grid(
                row=index + 1,
                column=1,
                padx=4,
                pady=3,
                sticky="w"
            )

    # ========================================================
    # 에디셔널
    # ========================================================

    def _build_additional_section(self):

        frame = self._section("에디셔널")

        # ----------------------------------------------------
        # 등급
        # ----------------------------------------------------

        ttk.Label(
            frame,
            text="등급"
        ).grid(
            row=0,
            column=0,
            padx=4,
            pady=3,
            sticky="e"
        )

        ttk.Combobox(
            frame,
            textvariable=self.additional_grade_var,
            values=POTENTIAL_GRADES,
            state="readonly",
            width=14
        ).grid(
            row=0,
            column=1,
            padx=4,
            pady=3,
            sticky="w"
        )

        # ----------------------------------------------------
        # 옵션
        # ----------------------------------------------------

        option_values = [
            option[0]
            for option in ADDITIONAL_OPTIONS
        ]

        for index, variable in enumerate(
            self.additional_vars
        ):

            ttk.Label(
                frame,
                text=f"{index + 1}."
            ).grid(
                row=index + 1,
                column=0,
                padx=4,
                pady=3,
                sticky="e"
            )

            ttk.Combobox(
                frame,
                textvariable=variable,
                values=option_values,
                state="readonly",
                width=22
            ).grid(
                row=index + 1,
                column=1,
                padx=4,
                pady=3,
                sticky="w"
            )

    # ========================================================
    # 가격
    # ========================================================

    def _build_price_section(self):

        frame = self._section("거래 정보")

        # ----------------------------------------------------
        # 가격
        # ----------------------------------------------------

        ttk.Label(
            frame,
            text="가격"
        ).grid(
            row=0,
            column=0,
            padx=4,
            pady=3,
            sticky="e"
        )

        ttk.Entry(
            frame,
            textvariable=self.price_var,
            width=10
        ).grid(
            row=0,
            column=1,
            padx=4,
            pady=3,
            sticky="w"
        )

        ttk.Label(
            frame,
            text="억"
        ).grid(
            row=0,
            column=2,
            padx=2,
            pady=3,
            sticky="w"
        )

        ttk.Checkbutton(
            frame,
            text="관세 +10%",
            variable=self.tax_var
        ).grid(
            row=0,
            column=3,
            padx=8,
            pady=3,
            sticky="w"
        )

        # ----------------------------------------------------
        # 가횟
        # ----------------------------------------------------

        ttk.Label(
            frame,
            text="가횟"
        ).grid(
            row=1,
            column=0,
            padx=4,
            pady=3,
            sticky="e"
        )

        ttk.Spinbox(
            frame,
            from_=0,
            to=10,
            textvariable=self.used_count_var,
            width=7
        ).grid(
            row=1,
            column=1,
            padx=4,
            pady=3,
            sticky="w"
        )

        ttk.Label(
            frame,
            text="/ 10"
        ).grid(
            row=1,
            column=2,
            padx=2,
            pady=3,
            sticky="w"
        )

    # ========================================================
    # 버튼
    # ========================================================

    def _build_buttons(self):

        frame = ttk.Frame(
            self
        )

        frame.pack(
            fill="x",
            padx=8,
            pady=8
        )

        ttk.Button(
            frame,
            text="취소",
            command=self._cancel
        ).pack(
            side="right",
            padx=4
        )

        if self.mode == "base":

            ttk.Button(
                frame,
                text="확인",
                command=self._set_base
            ).pack(
                side="right",
                padx=4
            )

        else:

            ttk.Button(
                frame,
                text="확인",
                command=self._add_item
            ).pack(
                side="right",
                padx=4
            )

    def _cancel(self):

        if self.on_close is not None:
            self.on_close()

    # ========================================================
    # 추옵 프리셋 적용
    # ========================================================

    def _apply_flame_preset(self, event=None):

        preset_name = (
            self.flame_preset_var.get()
        )

        if not preset_name:
            return

        preset = FLAME_PRESETS.get(
            preset_name
        )

        if preset is None:
            return

        # 기존값 초기화
        for variable in self.flame_entries.values():
            variable.set("")

        # 프리셋 적용
        for stat, value in preset.items():

            if stat in self.flame_entries:
                self.flame_entries[stat].set(
                    str(value)
                )

    # ========================================================
    # 작 프리셋 적용
    # ========================================================

    def _apply_scroll_preset(self, event=None):

        preset_name = (
            self.scroll_preset_var.get()
        )

        if not preset_name:
            return

        preset = SCROLL_PRESETS.get(
            preset_name
        )

        if preset is None:
            return

        # 기존값 초기화
        for variable in self.scroll_entries.values():
            variable.set("")

        # 프리셋 적용
        for stat, value in preset.items():

            if stat in self.scroll_entries:
                self.scroll_entries[stat].set(
                    str(value)
                )

    # ========================================================
    # 숫자
    # ========================================================

    @staticmethod
    def _get_int(variable):

        value = variable.get()

        if value is None:
            return 0

        text = str(value).strip()

        if not text:
            return 0

        return int(text)

    @staticmethod
    def _get_float(variable):

        value = variable.get()

        if value is None:
            return 0.0

        text = str(value).strip()

        if not text:
            return 0.0

        return float(text)

    # ========================================================
    # 일반 스탯 옵션 수집
    # ========================================================

    def _collect_options(
        self,
        entries
    ):
        options = []

        for stat, variable in entries.items():

            text = variable.get().strip()

            if not text:
                continue

            value = float(text)

            if value == 0:
                continue

            options.append(
                StatOption(
                    stat,
                    value
                )
            )

        return options

    # ========================================================
    # 잠재 옵션 변환
    # ========================================================

    @staticmethod
    def _find_option(
        selected,
        option_data
    ):
        """
        option_data:

            [
                ("INT +12%", "INT%", 12),
                ...
            ]

        selected 문자열을 StatOption으로 변환.
        """

        for display, stat, value in option_data:

            if display == selected:

                if stat == "":
                    return None

                return StatOption(
                    stat,
                    value
                )

        return None

    # ========================================================
    # 잠재 옵션 수집
    # ========================================================

    def _collect_potential_options(self):

        options = []

        for variable in self.potential_vars:

            selected = variable.get().strip()

            if not selected:
                continue

            option = self._find_option(
                selected,
                POTENTIAL_OPTIONS
            )

            if option is not None:
                options.append(option)

        return options

    # ========================================================
    # 에디 옵션 수집
    # ========================================================

    def _collect_additional_options(self):

        options = []

        for variable in self.additional_vars:

            selected = variable.get().strip()

            if not selected:
                continue

            option = self._find_option(
                selected,
                ADDITIONAL_OPTIONS
            )

            if option is not None:
                options.append(option)

        return options

    # ========================================================
    # Item 생성
    # ========================================================

    def _make_item(self):

        try:

            name = self.name_var.get().strip()

            price = self._get_float(
                self.price_var
            )

            starforce = self._get_int(
                self.starforce_var
            )

            used_count = self._get_int(
                self.used_count_var
            )

            flame_options = self._collect_options(
                self.flame_entries
            )

            scroll_options = self._collect_options(
                self.scroll_entries
            )

            potential_options = (
                self._collect_potential_options()
            )

            additional_options = (
                self._collect_additional_options()
            )

            return Item(
                name=name,

                slot=self.slot_var.get(),

                starforce=starforce,

                price=price,

                tax=self.tax_var.get(),

                used_count=used_count,

                max_count=10,

                flame_options=flame_options,

                scroll_options=scroll_options,

                potential_grade=(
                    self.potential_grade_var.get()
                ),

                potential_options=potential_options,

                additional_grade=(
                    self.additional_grade_var.get()
                ),

                additional_potential_options=(
                    additional_options
                )
            )

        except ValueError:

            messagebox.showerror(
                "입력 오류",
                "숫자를 입력하는 항목을 확인해주세요.",
                parent=self
            )

            return None

    # ========================================================
    # 공통 검증
    # ========================================================

    def _validate_item(self, item):

        if item is None:
            return False

        if not item.name:

            messagebox.showwarning(
                "입력 오류",
                "아이템 이름을 입력해주세요.",
                parent=self
            )

            return False

        if item.price < 0:

            messagebox.showwarning(
                "입력 오류",
                "가격은 0 이상이어야 합니다.",
                parent=self
            )

            return False

        if item.starforce < 0:

            messagebox.showwarning(
                "입력 오류",
                "스타포스는 0 이상이어야 합니다.",
                parent=self
            )

            return False

        if not 0 <= item.used_count <= item.max_count:

            messagebox.showwarning(
                "입력 오류",
                f"가횟은 0 ~ {item.max_count} 범위여야 합니다.",
                parent=self
            )

            return False

        return True

    # ========================================================
    # 기준 아이템
    # ========================================================

    def _set_base(self):

        item = self._make_item()

        if not self._validate_item(item):
            return

        self.on_base_set(item)

        self._cancel()

    # ========================================================
    # 경매장 매물
    # ========================================================

    def _add_item(self):

        item = self._make_item()

        if not self._validate_item(item):
            return

        self.on_item_add(item)

        self._cancel()

    # ========================================================
    # 초기화
    # ========================================================

    def clear(self):

        # ----------------------------------------------------
        # 기본
        # ----------------------------------------------------

        self.name_var.set("")

        if SLOTS:
            self.slot_var.set(
                SLOTS[0]
            )

        self.item_preset_var.set("1")

        # ----------------------------------------------------
        # 스타포스
        # ----------------------------------------------------

        self.starforce_var.set(0)

        # ----------------------------------------------------
        # 추옵
        # ----------------------------------------------------

        self.flame_preset_var.set("")

        for variable in self.flame_entries.values():
            variable.set("")

        # ----------------------------------------------------
        # 작
        # ----------------------------------------------------

        self.scroll_preset_var.set("")

        for variable in self.scroll_entries.values():
            variable.set("")

        # ----------------------------------------------------
        # 잠재
        # ----------------------------------------------------

        self.potential_grade_var.set(
            "레전드리"
        )

        for variable in self.potential_vars:
            variable.set("없음")

        # ----------------------------------------------------
        # 에디
        # ----------------------------------------------------

        self.additional_grade_var.set(
            "에픽"
        )

        for variable in self.additional_vars:
            variable.set("없음")

        # ----------------------------------------------------
        # 가격
        # ----------------------------------------------------

        self.price_var.set("")

        self.tax_var.set(False)

        self.used_count_var.set(0)