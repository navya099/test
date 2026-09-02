# gui/equipment_panel.py

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from config import DEFAULT_EQUIPMENT_NAMES


class EquipmentPanel(ttk.LabelFrame):

    def __init__(
        self,
        parent,
        manager,
        on_select
    ):
        super().__init__(
            parent,
            text="장비"
        )

        self.manager = manager
        self.on_select = on_select

        self.current_character = None
        self.selected_name = None

        self._build_ui()

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5,
            pady=5
        )

        control_frame = ttk.Frame(self)
        control_frame.pack(
            side="right",
            padx=5
        )

        ttk.Button(
            control_frame,
            text="+ 장비 추가",
            command=self._add_equipment
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            control_frame,
            text="현재 장비 삭제",
            command=self._delete_equipment
        ).pack(
            side="left",
            padx=2
        )

    # ========================================================
    # 캐릭터 변경
    # ========================================================

    def set_character(self, character):

        self.current_character = character
        self.selected_name = None

        self.refresh()

    # ========================================================
    # 갱신
    # ========================================================

    def refresh(self):

        for widget in self.button_frame.winfo_children():
            widget.destroy()

        if self.current_character is None:
            return

        for name in self.current_character.get_equipment_names():

            button = ttk.Button(
                self.button_frame,
                text=name,
                command=lambda n=name: self._select(n)
            )

            button.pack(
                side="left",
                padx=2
            )

    # ========================================================
    # 선택
    # ========================================================

    def _select(self, name):

        self.selected_name = name

        self.on_select(name)

    # ========================================================
    # 추가
    # ========================================================

    def _add_equipment(self):

        if self.current_character is None:
            return

        # 기본 장비 중 아직 없는 것 우선 표시
        available = [
            name
            for name in DEFAULT_EQUIPMENT_NAMES
            if name not in self.current_character.equipments
        ]

        if available:

            dialog_text = (
                "장비 이름을 입력하세요.\n\n"
                "기본 장비:\n"
                + ", ".join(available)
            )

        else:

            dialog_text = "장비 이름을 입력하세요."

        name = simpledialog.askstring(
            "장비 추가",
            dialog_text,
            parent=self
        )

        if not name:
            return

        name = name.strip()

        if not self.current_character.add_equipment(name):

            messagebox.showwarning(
                "추가 실패",
                "이미 존재하는 장비입니다.",
                parent=self
            )

            return

        self.refresh()

        self._select(name)

    # ========================================================
    # 삭제
    # ========================================================

    def _delete_equipment(self):

        if (
            self.current_character is None
            or self.selected_name is None
        ):
            return

        answer = messagebox.askyesno(
            "장비 삭제",
            f"'{self.selected_name}' 장비를 삭제하시겠습니까?\n"
            "해당 장비의 기준템과 모든 매물이 삭제됩니다.",
            parent=self
        )

        if not answer:
            return

        self.current_character.remove_equipment(
            self.selected_name
        )

        self.selected_name = None

        self.refresh()

        self.on_select(None)