# gui/efficiency_editor.py

import tkinter as tk
from tkinter import ttk, messagebox

from config import create_default_efficiency_table


class EfficiencyEditor(tk.Toplevel):

    def __init__(self, parent, character, on_apply):
        super().__init__(parent)

        self.character = character
        self.on_apply = on_apply

        self.title(
            f"효율 테이블 - {character.name}"
        )

        self.geometry("500x560")
        self.resizable(False, False)

        self.entries = {}

        self._build_ui()
        self._load_values()

        self.transient(parent)
        self.grab_set()

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        title = ttk.Label(
            self,
            text=f"{self.character.name} 효율 테이블",
            font=("맑은 고딕", 14, "bold")
        )

        title.pack(
            pady=(15, 10)
        )

        description = ttk.Label(
            self,
            text=(
                "각 스탯의 기준값과 해당 기준값이 가지는 "
                "최종데미지를 입력하세요."
            )
        )

        description.pack(
            pady=(0, 10)
        )

        container = ttk.Frame(self)
        container.pack(
            fill="both",
            expand=True,
            padx=15
        )

        headers = [
            ("스탯", 20),
            ("기준값", 12),
            ("최종뎀", 12),
        ]

        for column, (text, width) in enumerate(headers):

            ttk.Label(
                container,
                text=text,
                width=width,
                anchor="center"
            ).grid(
                row=0,
                column=column,
                padx=3,
                pady=4
            )

        for row, stat_name in enumerate(
            self.character.efficiency_table.keys(),
            start=1
        ):

            ttk.Label(
                container,
                text=stat_name,
                anchor="w"
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=3,
                pady=2
            )

            value_entry = ttk.Entry(
                container,
                width=12
            )

            value_entry.grid(
                row=row,
                column=1,
                padx=3,
                pady=2
            )

            final_entry = ttk.Entry(
                container,
                width=12
            )

            final_entry.grid(
                row=row,
                column=2,
                padx=3,
                pady=2
            )

            self.entries[stat_name] = (
                value_entry,
                final_entry
            )

        button_frame = ttk.Frame(self)
        button_frame.pack(
            pady=15
        )

        ttk.Button(
            button_frame,
            text="기본값 복원",
            command=self._reset
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="적용",
            command=self._apply
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            button_frame,
            text="취소",
            command=self.destroy
        ).pack(
            side="left",
            padx=5
        )

    # ========================================================
    # 값
    # ========================================================

    def _load_values(self):

        for stat_name, (
            value_entry,
            final_entry
        ) in self.entries.items():

            data = self.character.efficiency_table[
                stat_name
            ]

            value_entry.insert(
                0,
                str(data["value"])
            )

            final_entry.insert(
                0,
                str(data["final"])
            )

    # ========================================================
    # 기본값
    # ========================================================

    def _reset(self):

        default_table = create_default_efficiency_table()

        for stat_name, (
            value_entry,
            final_entry
        ) in self.entries.items():

            value_entry.delete(0, tk.END)
            final_entry.delete(0, tk.END)

            value_entry.insert(
                0,
                str(default_table[stat_name]["value"])
            )

            final_entry.insert(
                0,
                str(default_table[stat_name]["final"])
            )

    # ========================================================
    # 적용
    # ========================================================

    def _apply(self):

        new_table = {}

        try:

            for stat_name, (
                value_entry,
                final_entry
            ) in self.entries.items():

                value = float(
                    value_entry.get().strip()
                )

                final = float(
                    final_entry.get().strip()
                )

                if value <= 0:
                    raise ValueError(
                        f"{stat_name}: 기준값은 0보다 커야 합니다."
                    )

                new_table[stat_name] = {
                    "value": value,
                    "final": final,
                }

        except ValueError as error:

            messagebox.showerror(
                "입력 오류",
                str(error),
                parent=self
            )

            return

        self.character.set_efficiency_table(
            new_table
        )

        self.on_apply()

        self.destroy()