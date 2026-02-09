import tkinter as tk
from tkinter import ttk

from gui.viewmodel.equipment_vm import EquipmentVM


class EquipMentWindow(ttk.LabelFrame):
    def __init__(self, master ,event, lib_manager):
        super().__init__(master, text="추가 장비 정보")
        self.equips: list[EquipmentVM] = []  # 리스트로 장비 DTO 관리
        self.master = master
        self.event = event
        self.lib_manager = lib_manager
        self.rails = []  # TKRailData 목록
        self.event.bind("rails.updated", self._on_rails_updated)
        #장비 리스트
        self.equip_name_list = self.lib_manager.list_all_files(group='base')
        # 파일명 .csv제거
        self.equip_name_list = [
            name.removesuffix(".csv") for name in self.lib_manager.list_all_files(group='base')
        ]

        # 프레임 생성
        self.equip_frame = ttk.LabelFrame(self, text='장비 설정')
        self.equip_frame.grid(row=0, column=0, columnspan=2, sticky="w")

        # 추가/삭제 버튼
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=1, column=0, sticky="w", pady=5)
        ttk.Button(self.button_frame, text="+", width=3, command=self.add_equip).grid(row=0, column=0, padx=2)
        ttk.Button(self.button_frame, text="-", width=3, command=self.remove_equip).grid(row=0, column=1, padx=2)

        self.build_equip_frame()

    def _on_rails_updated(self, rails):
        # rails: BracketFrame.bracket_vars
        self.rails = rails

    def build_equip_frame(self):
        # 기존 UI 제거
        for w in self.equip_frame.winfo_children():
            w.destroy()

        headers = ["장비명", "위치 X", "위치 Y", '회전', '설치 레일', "설정"]
        for col, text in enumerate(headers):
            ttk.Label(self.equip_frame, text=text, font=("맑은 고딕", 9, "bold")).grid(
                row=0, column=col, padx=5, pady=2
            )

        for i, equip in enumerate(self.equips):
            row = i + 1

            # 기존 값 그대로 유지
            equip.name_var = tk.StringVar(value=equip.name_var.get())
            equip.x_var = tk.DoubleVar(value=equip.x_var.get())
            equip.y_var = tk.DoubleVar(value=equip.y_var.get())
            equip.rotation_var = tk.DoubleVar(value=equip.rotation_var.get())
            equip.base_rail_var = tk.IntVar(value=equip.base_rail_var.get())

            # 🟢 장비명 Combobox
            name_cb = ttk.Combobox(
                self.equip_frame,
                textvariable=equip.name_var,
                values=self.equip_name_list,
                width=20,
                state="readonly"  # 입력 불가, 목록에서만 선택
            )
            name_cb.grid(row=row, column=0)

            ttk.Entry(self.equip_frame, textvariable=equip.x_var, width=6).grid(row=row, column=1)
            ttk.Entry(self.equip_frame, textvariable=equip.y_var, width=6).grid(row=row, column=2)
            ttk.Entry(self.equip_frame, textvariable=equip.rotation_var, width=6).grid(row=row, column=3)

            # 🔹 레일 콤보박스
            if hasattr(self, "rails") and self.rails:
                rail_labels = [f"{r.name_var.get()} ({r.index_var.get()})" for r in self.rails]
                rail_cb = ttk.Combobox(
                    self.equip_frame,
                    values=rail_labels,
                    width=18,
                    state="readonly"
                )
                # 선택된 레일 설정
                selected_idx = next(
                    (idx for idx, r in enumerate(self.rails) if r.index_var.get() == equip.base_rail_var.get()),
                    0
                )
                rail_cb.current(selected_idx)

                def on_rail_selected(event, eq=equip, cb=rail_cb):
                    idx = cb.current()
                    if idx >= 0:
                        eq.base_rail_var.set(self.rails[idx].index_var.get())

                rail_cb.bind("<<ComboboxSelected>>", on_rail_selected)
                rail_cb.grid(row=row, column=4)

            ttk.Button(self.equip_frame, text="편집", command=lambda e=equip: self.edit_equip(e)).grid(row=row, column=5)


    def add_equip(self):
        # 새 장비 DTO 생성
        new_equip = EquipmentVM(
            name_var=tk.StringVar(value="장비1"),
            x_var=tk.DoubleVar(value=0),
            y_var=tk.DoubleVar(value=0),
            rotation_var=tk.DoubleVar(value=0),
            base_rail_var=tk.IntVar(value=0))
        self.equips.append(new_equip)
        self.build_equip_frame()
        self.event.emit("equips.updated", self.equips)

    def remove_equip(self):
        if self.equips:
            self.equips.pop()  # 마지막 장비 제거
            self.build_equip_frame()
            self.event.emit("equips.updated", self.equips)

    def edit_equip(self, equip):
        # 장비 편집 창 열기
        print("Edit equip:", equip.name_var.get())
        # 필요하면 BracketConfigWindow처럼 편집 창 구현 가능

    def load_from_dto(self, dto_list):
        """
        DTO 리스트로부터 VM 생성 후 UI 갱신
        dto_list: list of dict
            각 dict 구조:
            {
                "name": str,
                "x": float,
                "y": float,
                "rotation": float,
                "base_rail": int
            }
        """
        self.equips.clear()

        for dto in dto_list:
            vm = EquipmentVM(
                name_var=tk.StringVar(value=dto.get("name", "장비1")),
                x_var=tk.DoubleVar(value=dto.get("x", 0.0)),
                y_var=tk.DoubleVar(value=dto.get("y", 0.0)),
                rotation_var=tk.DoubleVar(value=dto.get("rotation", 0.0)),
                base_rail_var=tk.IntVar(value=dto.get("base_rail", 0)),
            )
            self.equips.append(vm)

        # UI 갱신
        self.build_equip_frame()
        self.event.emit("equips.updated", self.equips)
