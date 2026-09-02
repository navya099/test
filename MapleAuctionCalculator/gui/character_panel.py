# gui/character_panel.py

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox


class CharacterPanel(ttk.LabelFrame):

    def __init__(
        self,
        parent,
        manager,
        on_select
    ):
        super().__init__(
            parent,
            text="캐릭터"
        )

        self.manager = manager
        self.on_select = on_select

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
            text="+ 캐릭터 추가",
            command=self._add_character
        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(
            control_frame,
            text="현재 캐릭터 삭제",
            command=self._delete_character
        ).pack(
            side="left",
            padx=2
        )

    # ========================================================
    # 갱신
    # ========================================================

    def refresh(self):

        for widget in self.button_frame.winfo_children():
            widget.destroy()

        for name in self.manager.get_names():

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

    def _add_character(self):

        name = simpledialog.askstring(
            "캐릭터 추가",
            "캐릭터 이름을 입력하세요.",
            parent=self
        )

        if not name:
            return

        name = name.strip()

        if not self.manager.add_character(name):

            messagebox.showwarning(
                "추가 실패",
                "이미 존재하는 캐릭터입니다.",
                parent=self
            )

            return

        self.refresh()

        self._select(name)

    # ========================================================
    # 삭제
    # ========================================================

    def _delete_character(self):

        if not self.selected_name:
            return

        answer = messagebox.askyesno(
            "캐릭터 삭제",
            f"'{self.selected_name}' 캐릭터를 삭제하시겠습니까?\n"
            "해당 캐릭터의 모든 장비와 매물이 삭제됩니다.",
            parent=self
        )

        if not answer:
            return

        self.manager.remove_character(
            self.selected_name
        )

        self.selected_name = None

        self.refresh()

        self.on_select(None)