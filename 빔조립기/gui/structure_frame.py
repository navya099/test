from tkinter import ttk
import tkinter as tk

from Electric.Overhead.Pole import poletype
from gui.viewmodel.pole_vm import PoleVM


class StructureFrame(ttk.LabelFrame):
    def __init__(self, master, event):
        super().__init__(master, text="구조물 정보")
        self.event = event
        self.beam_vars = []
        self.pole_vars = []
        self.rails = []  # TKRailData 목록
        self.event.bind("rails.updated", self._on_rails_updated)
        self.pole_frame = ttk.LabelFrame(self, text='전주 설정')
        self.pole_frame.grid(row=0, column=0, columnspan=2, sticky="w")
        self.beam_frame = ttk.LabelFrame(self, text="빔 설정")
        self.beam_frame.grid(row=1, column=0, columnspan=2, sticky="w")
        self.event.bind("basic.changed", self._on_basic_changed)
        self._on_basic_changed()  # 초기 상태 반영

    def _on_rails_updated(self, rails):
        self.rails = rails
        self._refresh_pole_rail_combos()


    def _on_basic_changed(self, *_):
        # 전주는 항상 표시
        self.pole_frame.grid()
        self._rebuild_poles()

        # 빔은 옵션에 따라
        if not self.master.basic_frame.isbeaminstall.get():
            self.beam_frame.grid_remove()
            return

        self.beam_frame.grid()
        self._rebuild_beams()
    def _rebuild_beams(self, *_):
        for w in self.beam_frame.winfo_children():
            w.destroy()

        self.beam_vars.clear()

        headers = ["NO", "빔 타입", '설치 전주']
        for col, text in enumerate(headers):
            ttk.Label(
                self.beam_frame,
                text=text,
                font=("맑은 고딕", 9, "bold")
            ).grid(row=0, column=col, padx=5, pady=2)

        for i in range(self.master.beam_count.get()):
            row = i + 1
            ttk.Label(self.beam_frame, text=str(i + 1))\
                .grid(row=row, column=0)

            var = tk.StringVar(value="트러스빔")
            ttk.Combobox(
                self.beam_frame,
                textvariable=var,
                values=["강관빔", "트러스빔", "트러스라멘빔", "V트러스빔"],
                state="readonly",
                width=15
            ).grid(row=row, column=1)

            self.beam_vars.append(var)

    def _rebuild_poles(self, *_):
        for w in self.pole_frame.winfo_children():
            w.destroy()

        self.pole_vars.clear()

        headers = ["NO", '설치 레일',"전주 타입", '전주 규격', '전주 길이', ]
        for col, text in enumerate(headers):
            ttk.Label(
                self.pole_frame,
                text=text,
                font=("맑은 고딕", 9, "bold")
            ).grid(row=0, column=col, padx=5, pady=2)

        for i in range(self.master.pole_count.get()):
            row = i + 1
            ttk.Label(self.pole_frame, text=str(i + 1))\
                .grid(row=row, column=0)

            rail_labels = [
                f"{rail.name_var.get()} ({rail.index_var.get()})"
                for rail in self.rails
            ]
            # 1️⃣ 변수 먼저
            base_rail_var = tk.StringVar()
            poletypevar = tk.StringVar(value="강관주")
            polespec_var = tk.StringVar(value="P10")
            length_var = tk.DoubleVar(value=9.0)

            # 2️⃣ PoleVM 생성 (상태의 근원)
            pole_vm = PoleVM(
                index=tk.IntVar(value=row),
                poletype=poletypevar,
                polespec=polespec_var,
                pole_length=length_var,
                base_rail_index=tk.IntVar(value=0),
                base_rail_uid=tk.StringVar(value='')
            )
            self.pole_vars.append(pole_vm)

            # 3️⃣ UI 생성 (뷰)
            base_rail_cb = ttk.Combobox(
                self.pole_frame,
                textvariable=base_rail_var,
                values=rail_labels,
                state="readonly",
                width=18
            )
            base_rail_cb.grid(row=row, column=1)

            base_rail_cb._pole_vm = pole_vm  # ✅ 이제 안전
            # ✅ 여기!
            # 기본값은 "아직 선택된 게 없을 때만"
            if self.rails and not pole_vm.base_rail_uid.get():
                pole_vm.base_rail_uid.set(self.rails[0].uid)
                base_rail_cb.current(0)

            ttk.Combobox(
                self.pole_frame,
                textvariable=poletypevar,
                values=["강관주", "H형주", "조립철주"],
                state="readonly",
                width=15
            ).grid(row=row, column=2)

            ttk.Combobox(
                self.pole_frame,
                textvariable=polespec_var,
                values=["P10", "P12", "P14", "P16", "P18", "P20"],
                state="readonly",
                width=15
            ).grid(row=row, column=3)

            tk.Entry(
                self.pole_frame,
                textvariable=length_var,
                width=6
            ).grid(row=row, column=4)

            # 4️⃣ 이벤트 연결
            self._bind_base_rail(base_rail_cb, pole_vm)

    def _refresh_pole_rail_combos(self):
        rail_labels = [
            f"{rail.name_var.get()} ({rail.index_var.get()})"
            for rail in self.rails
        ]
        rail_uid_map = [rail.uid for rail in self.rails]

        for child in self.pole_frame.winfo_children():
            if not isinstance(child, ttk.Combobox) or child.cget("width") != 18:
                continue

            pole_vm = getattr(child, "_pole_vm", None)
            if not pole_vm:
                continue

            # 1️⃣ values만 갱신
            child["values"] = rail_labels

            # 2️⃣ 상태는 VM에서만 읽음
            uid = pole_vm.base_rail_uid.get()

            if uid in rail_uid_map:
                child.current(rail_uid_map.index(uid))
            else:
                child.set("")  # 없는 rail이면 비움

    def _bind_base_rail(self, cb, pole_vm):
        def on_select(_):
            idx = cb.current()
            if idx >= 0:
                pole_vm.base_rail_uid.set(
                    self.rails[idx].uid
                )

        cb.bind("<<ComboboxSelected>>", on_select)


