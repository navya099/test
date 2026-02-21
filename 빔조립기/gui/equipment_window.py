import tkinter as tk
from tkinter import ttk

from gui.viewmodel.equipment_vm import EquipmentVM


class EquipMentWindow(ttk.LabelFrame):
    def __init__(self, master ,event, lib_manager):
        super().__init__(master, text="추가 장비 정보")
        self.master = master
        self.event = event
        self.current_section = None
        self.lib_manager = lib_manager
        if self.event:
            self.event.bind("section.selected", self._on_section_selected)
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

    def _on_section_selected(self, section):
        self.current_section = section
        if section:
            if self.current_section.equips_var:
                self.refresh_equips() #기존 객체 UI갱신
            else:
                self.rebuild_equips() #새 객세 생성
        else:
            return

    def _on_rails_updated(self):
        if self.current_section.equips_var:
            # UI 갱신만
            self.refresh_equips()

    def rebuild_equips(self, *_):
        """
        - 구간이 처음 생성되었을 때만 호출해서 EquipVM들을 새로 만들어줍니다.
        - 데이터 모델 초기화 역할만 담당합니다.
        """
        # 기존 UI 제거
        for w in self.equip_frame.winfo_children():
            w.destroy()

        # ✅ equips 초기화는 rebuild에서만
        self.current_section.equips_var.clear()

        # EquipVM 새로 생성
        for i in self.current_section.equips_var:
            equip_vm = EquipmentVM(
                name_var=tk.StringVar(value="기본장비"),
                x_var=tk.DoubleVar(value=0.0),
                y_var=tk.DoubleVar(value=0.0),
                rotation_var=tk.DoubleVar(value=0.0),
                base_rail_index_var=tk.IntVar(value=0)
            )
            self.current_section.equips_var.append(equip_vm)

        # ✅ UI는 refresh에서 따로 그림
        self.refresh_equips()

    def refresh_equips(self):
        """
        - 이미 존재하는 EquipVM들을 그대로 사용해서 UI만 다시 그려줍니다.
        - 상태 보존 + UI 갱신 역할을 담당합니다.
        """
        # 기존 UI 제거
        for w in self.equip_frame.winfo_children():
            w.destroy()

        headers = ["장비명", "위치 X", "위치 Y", '회전', '설치 레일', "설정"]
        for col, text in enumerate(headers):
            ttk.Label(self.equip_frame, text=text, font=("맑은 고딕", 9, "bold")).grid(
                row=0, column=col, padx=5, pady=2
            )

        for i, equip in enumerate(self.current_section.equips_var, start=1):
            row = i

            # 장비명 Combobox
            name_cb = ttk.Combobox(
                self.equip_frame,
                textvariable=equip.name_var,
                values=self.equip_name_list,
                width=20,
                state="readonly"
            )
            name_cb.grid(row=row, column=0)

            # 위치/회전 Entry
            ttk.Entry(self.equip_frame, textvariable=equip.x_var, width=6).grid(row=row, column=1)
            ttk.Entry(self.equip_frame, textvariable=equip.y_var, width=6).grid(row=row, column=2)
            ttk.Entry(self.equip_frame, textvariable=equip.rotation_var, width=6).grid(row=row, column=3)

            # 레일 콤보박스
            if self.current_section.rails_var:
                rail_labels = [f"{r.name_var.get()} ({r.index_var.get()})" for r in self.current_section.rails_var]
                rail_cb = ttk.Combobox(
                    self.equip_frame,
                    values=rail_labels,
                    width=18,
                    state="readonly"
                )

                selected_idx = next(
                    (idx for idx, r in enumerate(self.current_section.rails_var)
                     if r.index_var.get() == equip.base_rail_index_var.get()),
                    0
                )
                rail_cb.current(selected_idx)
                equip.base_rail_index_var.set(self.current_section.rails_var[selected_idx].index_var.get())

                def on_rail_selected(event, eq=equip, cb=rail_cb):
                    idx = cb.current()
                    if idx >= 0:
                        new_val = self.current_section.rails_var[idx].index_var.get()
                        eq.base_rail_index_var.set(new_val)
                        print(f"[DEBUG] {eq.name_var.get()} rail index updated to {new_val}")

                rail_cb.bind("<<ComboboxSelected>>", on_rail_selected)
                rail_cb.grid(row=row, column=4)

            # 편집 버튼
            ttk.Button(self.equip_frame, text="편집", command=lambda e=equip: self.edit_equip(e)).grid(row=row, column=5)
    def add_equip(self):
        # 새 장비 DTO 생성
        new_equip = EquipmentVM(
            name_var=tk.StringVar(value="장비1"),
            x_var=tk.DoubleVar(value=0),
            y_var=tk.DoubleVar(value=0),
            rotation_var=tk.DoubleVar(value=0),
            base_rail_index_var=tk.IntVar(value=0))
        self.current_section.equips_var.append(new_equip)
        self.refresh_equips()
        self.event.emit("equips.updated")

    def remove_equip(self):
        if self.current_section.equips_var:
            self.current_section.equips_var.pop()  # 마지막 장비 제거
            self.rebuild_equips()
            self.event.emit("equips.updated")

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
                x_var=tk.DoubleVar(value=dto.get("xoffset", 0.0)),
                y_var=tk.DoubleVar(value=dto.get("yoffset", 0.0)),
                rotation_var=tk.DoubleVar(value=dto.get("rotation", 0.0)),
                base_rail_index_var=tk.IntVar(value=dto.get("base_rail_index", 0)),
            )
            self.equips.append(vm)

        # UI 갱신
        self.refresh_equips()
        self.event.emit("equips.updated", self.equips)
