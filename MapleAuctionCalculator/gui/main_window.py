# gui/main_window.py

import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from calculator import Calculator
from storage import JsonStorage

from gui.character_panel import CharacterPanel
from gui.equipment_panel import EquipmentPanel
from gui.item_panel import ItemPanel
from gui.result_table import ResultTable
from gui.efficiency_editor import EfficiencyEditor


class MainWindow:

    def __init__(self, root, manager):

        self.root = root
        self.manager = manager

        self.current_character = None
        self.current_equipment = None

        self._build_ui()

        # 저장파일이 아무것도 없을 때 기본 캐릭터 생성
        if not self.manager.get_names():
            self.manager.add_character("캐릭터 1")

        self.character_panel.refresh()

        first_character = (
            self.manager.get_names()[0]
        )

        self.select_character(first_character)

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        self.root.title(
            "메이플 경매장 장비 가성비 계산기"
        )

        self.root.geometry(
            "1500x900"
        )

        self.root.minsize(
            1100,
            700
        )

        # ----------------------------------------------------
        # 상단 메뉴
        # ----------------------------------------------------

        top_frame = ttk.Frame(
            self.root
        )

        top_frame.pack(
            fill="x",
            padx=8,
            pady=5
        )

        ttk.Button(
            top_frame,
            text="💾 전체 저장",
            command=self.save_all
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            top_frame,
            text="📂 전체 불러오기",
            command=self.load_all
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            top_frame,
            text="⚙ 캐릭터 효율 테이블",
            command=self.open_efficiency_editor
        ).pack(
            side="left",
            padx=3
        )

        # ----------------------------------------------------
        # 캐릭터
        # ----------------------------------------------------

        self.character_panel = CharacterPanel(
            self.root,
            self.manager,
            self.select_character
        )

        self.character_panel.pack(
            fill="x",
            padx=8,
            pady=3
        )

        # ----------------------------------------------------
        # 장비
        # ----------------------------------------------------

        self.equipment_panel = EquipmentPanel(
            self.root,
            self.manager,
            self.select_equipment
        )

        self.equipment_panel.pack(
            fill="x",
            padx=8,
            pady=3
        )

        # ----------------------------------------------------
        # 현재 상태
        # ----------------------------------------------------

        self.status_label = ttk.Label(
            self.root,
            text="현재 선택 없음",
            font=("맑은 고딕", 11, "bold")
        )

        self.status_label.pack(
            anchor="w",
            padx=12,
            pady=5
        )

        # ----------------------------------------------------
        # 아이템 입력
        # ----------------------------------------------------

        item_button_frame = ttk.Frame(
            self.root
        )

        item_button_frame.pack(
            fill="x",
            padx=8,
            pady=5
        )

        ttk.Button(
            item_button_frame,
            text="기준 아이템 설정",
            command=self.open_base_item_panel
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            item_button_frame,
            text="경매장 매물 추가",
            command=self.open_auction_item_panel
        ).pack(
            side="left",
            padx=3
        )

        # ----------------------------------------------------
        # 결과
        # ----------------------------------------------------

        self.result_table = ResultTable(
            self.root
        )

        self.result_table.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=5
        )

        # ----------------------------------------------------
        # 하단 버튼
        # ----------------------------------------------------

        bottom_frame = ttk.Frame(
            self.root
        )

        bottom_frame.pack(
            fill="x",
            padx=8,
            pady=5
        )

        ttk.Button(
            bottom_frame,
            text="선택 매물 삭제",
            command=self.delete_selected_item
        ).pack(
            side="left",
            padx=3
        )

        ttk.Button(
            bottom_frame,
            text="현재 장비 매물 전체 삭제",
            command=self.clear_current_items
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

    # ========================================================
    # 캐릭터 선택
    # ========================================================

    def select_character(self, name):

        self.current_character = None
        self.current_equipment = None

        if name is None:
            self.equipment_panel.set_character(None)

            self.status_label.config(
                text="현재 선택 없음"
            )

            self.result_table.clear()

            return

        character = self.manager.get_character(
            name
        )

        if character is None:
            return

        self.current_character = character

        self.character_panel.selected_name = name

        self.equipment_panel.set_character(
            character
        )

        self.result_table.clear()

        self.status_label.config(
            text=f"캐릭터: {character.name} | 장비: 선택 없음"
        )

    # ========================================================
    # 장비 선택
    # ========================================================

    def select_equipment(self, name):

        if self.current_character is None:
            return

        if name is None:
            self.current_equipment = None

            self.result_table.clear()

            self.status_label.config(
                text=(
                    f"캐릭터: {self.current_character.name}"
                    " | 장비: 선택 없음"
                )
            )

            return

        equipment = (
            self.current_character.get_equipment(name)
        )

        if equipment is None:
            return

        self.current_equipment = equipment

        self.equipment_panel.selected_name = name

        self.refresh_results()

        self.status_label.config(
            text=(
                f"캐릭터: {self.current_character.name}"
                f" | 장비: {equipment.name}"
            )
        )

    # ========================================================
    # 기준템
    # ========================================================

    def set_base_item(self, item):

        if self.current_equipment is None:

            messagebox.showwarning(
                "선택 필요",
                "먼저 장비를 선택해주세요.",
                parent=self.root
            )

            return

        self.current_equipment.set_base(
            item
        )

        self.refresh_results()

        messagebox.showinfo(
            "완료",
            "기준 아이템을 설정했습니다.",
            parent=self.root
        )

    # ========================================================
    # 매물 추가
    # ========================================================

    def add_auction_item(self, item):

        if self.current_equipment is None:

            messagebox.showwarning(
                "선택 필요",
                "먼저 장비를 선택해주세요.",
                parent=self.root
            )

            return

        self.current_equipment.add_item(
            item
        )

        self.refresh_results()

    # ========================================================
    # 결과 계산
    # ========================================================

    def refresh_results(self):

        self.result_table.clear()

        if (
            self.current_character is None
            or self.current_equipment is None
        ):
            return

        equipment = self.current_equipment

        if equipment.base_item is None:
            return

        results = list(
            equipment.items
        )

        results.sort(
            key=lambda item:
                Calculator.ranking_score(
                    item,
                    equipment.base_item,
                    self.current_character
                ),
            reverse=True
        )

        self.result_table.show_results(
            results,
            equipment.base_item,
            Calculator,
            self.current_character
        )

    # ========================================================
    # 매물 삭제
    # ========================================================

    def delete_selected_item(self):

        if self.current_equipment is None:
            return

        index = (
            self.result_table.get_selected_index()
        )

        if index is None:
            messagebox.showwarning(
                "선택 필요",
                "삭제할 매물을 선택해주세요.",
                parent=self.root
            )

            return

        # 현재 결과는 정렬된 상태이므로
        # 결과 테이블의 순위와 원본 리스트가 다를 수 있다.
        results = list(
            self.current_equipment.items
        )

        results.sort(
            key=lambda item:
                Calculator.ranking_score(
                    item,
                    self.current_equipment.base_item,
                    self.current_character
                ),
            reverse=True
        )

        target = results[index]

        self.current_equipment.items.remove(
            target
        )

        self.refresh_results()

    # ========================================================
    # 전체 삭제
    # ========================================================

    def clear_current_items(self):

        if self.current_equipment is None:
            return

        answer = messagebox.askyesno(
            "전체 삭제",
            "현재 장비의 모든 매물을 삭제하시겠습니까?",
            parent=self.root
        )

        if not answer:
            return

        self.current_equipment.clear_items()

        self.refresh_results()

    # ========================================================
    # 효율표
    # ========================================================

    def open_efficiency_editor(self):

        if self.current_character is None:

            messagebox.showwarning(
                "선택 필요",
                "먼저 캐릭터를 선택해주세요.",
                parent=self.root
            )

            return

        EfficiencyEditor(
            self.root,
            self.current_character,
            self._efficiency_changed
        )

    def _efficiency_changed(self):

        self.refresh_results()

    # ========================================================
    # 전체 저장
    # ========================================================

    def save_all(self):

        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="전체 데이터 저장",
            defaultextension=".json",
            filetypes=[
                ("JSON 파일", "*.json"),
                ("모든 파일", "*.*"),
            ]
        )

        if not filepath:
            return

        try:

            JsonStorage.save(
                self.manager,
                filepath
            )

            messagebox.showinfo(
                "저장 완료",
                "전체 데이터를 저장했습니다.",
                parent=self.root
            )

        except Exception as error:

            messagebox.showerror(
                "저장 오류",
                str(error),
                parent=self.root
            )

    # ========================================================
    # 전체 불러오기
    # ========================================================

    def load_all(self):

        filepath = filedialog.askopenfilename(
            parent=self.root,
            title="전체 데이터 불러오기",
            filetypes=[
                ("JSON 파일", "*.json"),
                ("모든 파일", "*.*"),
            ]
        )

        if not filepath:
            return

        try:

            JsonStorage.load(
                self.manager,
                filepath
            )

        except Exception as error:

            messagebox.showerror(
                "불러오기 오류",
                str(error),
                parent=self.root
            )

            return

        self.character_panel.refresh()

        names = self.manager.get_names()

        if names:
            self.select_character(
                names[0]
            )
        else:
            self.select_character(None)

        messagebox.showinfo(
            "불러오기 완료",
            "전체 데이터를 불러왔습니다.",
            parent=self.root
        )

    # ========================================================
    # CSV
    # ========================================================

    def export_csv(self):

        if (
            self.current_character is None
            or self.current_equipment is None
        ):
            messagebox.showwarning(
                "선택 필요",
                "캐릭터와 장비를 선택해주세요.",
                parent=self.root
            )

            return

        equipment = self.current_equipment

        if equipment.base_item is None:
            messagebox.showwarning(
                "기준템 필요",
                "먼저 기준 아이템을 설정해주세요.",
                parent=self.root
            )

            return

        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            title="CSV 저장",
            defaultextension=".csv",
            filetypes=[
                ("CSV 파일", "*.csv"),
                ("모든 파일", "*.*"),
            ]
        )

        if not filepath:
            return

        results = list(
            equipment.items
        )

        results.sort(
            key=lambda item:
                Calculator.ranking_score(
                    item,
                    equipment.base_item,
                    self.current_character
                ),
            reverse=True
        )

        base = equipment.base_item

        with open(
            filepath,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "캐릭터",
                "장비",
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
                "잔여 가횟",
                "가성비",
            ])

            for rank, item in enumerate(
                results,
                start=1
            ):

                damage = Calculator.final_damage(
                    item,
                    self.current_character
                )

                base_damage = Calculator.final_damage(
                    base,
                    self.current_character
                )

                difference = (
                    damage - base_damage
                )

                price_difference = (
                    item.actual_price
                    - base.actual_price
                )

                efficiency = (
                    Calculator.efficiency_score(
                        item,
                        base,
                        self.current_character
                    )
                )

                if efficiency == float("inf"):
                    efficiency_text = "∞"
                else:
                    efficiency_text = f"{efficiency:.6f}"

                writer.writerow([
                    self.current_character.name,
                    equipment.name,
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
                    f"{item.remaining_count}/{item.max_count}",
                    efficiency_text,
                ])

        messagebox.showinfo(
            "저장 완료",
            "CSV 파일을 저장했습니다.",
            parent=self.root
        )

    # ========================================================
    # 아이템 입력 창
    # ========================================================

    def open_base_item_panel(self):

        if self.current_equipment is None:
            messagebox.showwarning(
                "선택 필요",
                "먼저 장비를 선택해주세요.",
                parent=self.root
            )

            return

        self._open_item_panel(
            mode="base"
        )

    def open_auction_item_panel(self):

        if self.current_equipment is None:
            messagebox.showwarning(
                "선택 필요",
                "먼저 장비를 선택해주세요.",
                parent=self.root
            )

            return

        self._open_item_panel(
            mode="auction"
        )

    def _open_item_panel(self, mode):

        window = tk.Toplevel(
            self.root
        )

        if mode == "base":
            window.title(
                "기준 아이템 설정"
            )
        else:
            window.title(
                "경매장 매물 추가"
            )

        window.resizable(
            False,
            False
        )

        # ----------------------------------------
        # ItemPanel
        # ----------------------------------------

        panel = ItemPanel(
            window,
            on_base_set=self.set_base_item,
            on_item_add=self.add_auction_item,
            mode=mode,
            on_close=window.destroy
        )

        panel.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # ----------------------------------------
        # 모달 창
        # ----------------------------------------

        window.transient(
            self.root
        )

        window.grab_set()

        # 부모 창 중앙에 배치
        self.root.update_idletasks()

        x = (
                self.root.winfo_x()
                + (self.root.winfo_width() - window.winfo_reqwidth()) // 2
        )

        y = (
                self.root.winfo_y()
                + (self.root.winfo_height() - window.winfo_reqheight()) // 2
        )

        window.geometry(
            f"+{max(x, 0)}+{max(y, 0)}"
        )

        window.focus_force()