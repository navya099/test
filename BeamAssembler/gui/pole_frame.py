from tkinter import ttk
import tkinter as tk
from gui.viewmodel.pole_vm import PoleVM
from gui.viewmodel.polebasevm import PoleBaseVM


class PoleFrame(ttk.LabelFrame):
    def __init__(self, master, event=None):
        super().__init__(master, text="전주 정보")
        self.current_section = None
        self.event = event
        self.isloading = False
        if event:
            self.event.bind("section.selected", self._on_section_selected)
            self.event.bind("rails.updated", self._on_rails_updated)
            self.event.bind("basic.changed", self._on_basic_changed)

        self._build_empty()

    def _on_section_selected(self, section):
        self.current_section = section
        if self.current_section.poles_var:
            self.refresh_poles() #기존 객체 UI갱신
        else:
            self.rebuild_poles() #새 객세 생성

    def _refresh_pole_rail_combos(self):
        rail_labels = [
            f"{rail.name_var.get()} ({rail.index_var.get()})"
            for rail in self.current_section.rails_var
        ]
        rail_uid_map = [rail.uid for rail in self.current_section.rails_var]

        for child in self.winfo_children():
            if not isinstance(child, ttk.Combobox) or child.cget("width") != 18:
                continue

            pole_vm = getattr(child, "_pole_vm", None)
            if not pole_vm:
                continue

            child["values"] = rail_labels

            uid = pole_vm.base_rail_uid.get()

            if uid in rail_uid_map:
                idx = rail_uid_map.index(uid)
                child.current(rail_uid_map.index(uid))
                # 🔥🔥🔥 핵심 추가
                pole_vm.base_rail_index.set(
                    self.current_section.rails_var[idx].index_var.get()
                )

            else:
                child.set("")

    def _on_basic_changed(self, *_):
        if getattr(self, "isloading", False):
            return  # 🔥 로딩 중이면 rebuild 금지

        self.grid()
        self.rebuild_poles()

    def _build_empty(self):
        """구간이 없을 때 기본 UI"""
        headers = ["NO", '설치 레일', "전주 타입", '전주 규격', '전주 길이', '건식게이지']
        for col, text in enumerate(headers):
            ttk.Label(self, text=text, font=("맑은 고딕", 9, "bold")).grid(row=0, column=col, padx=5, pady=2)

        # 기본값 없는 빈 Entry들
        for i in range(1, 2):  # 예시로 2행만 표시
            ttk.Label(self, text=str(i)).grid(row=i, column=0)
            ttk.Entry(self, width=15).grid(row=i, column=1)
            ttk.Entry(self, width=15).grid(row=i, column=2)
            ttk.Entry(self, width=15).grid(row=i, column=3)
            ttk.Entry(self, width=6).grid(row=i, column=4)
            ttk.Entry(self, width=6).grid(row=i, column=5)

    def _on_rails_updated(self):
        self._refresh_pole_rail_combos()

    def rebuild_poles(self, *_):
        """
        - 구간이 처음 생성되었을 때만 호출해서 PoleVM들을 새로 만들어줍니다.
        - 데이터 모델 초기화 역할만 담당
        """
        for w in self.winfo_children():
            w.destroy()

        # ✅ poles_var 초기화는 rebuild에서만
        self.current_section.poles_var.clear()

        headers = ["NO", '설치 레일',"전주 타입", '전주 규격', '전주 길이','건식게이지']
        for col, text in enumerate(headers):
            ttk.Label(self, text=text, font=("맑은 고딕", 9, "bold")).grid(row=0, column=col, padx=5, pady=2)

        for i in range(self.current_section.pole_count_var.get()):
            # PoleVM 새로 생성
            pole_vm = PoleVM(
                index=tk.IntVar(value=i + 1),
                poletype=tk.StringVar(value="강관주"),
                polespec=tk.StringVar(value="P10"),
                pole_length=tk.DoubleVar(value=9.0),
                base_rail_index=tk.IntVar(value=0),
                base_rail_uid=tk.StringVar(value=''),
                gauge=tk.DoubleVar(value=3.0),
                foundation=PoleBaseVM(basename_var=tk.StringVar(value='')),
            )
            self.current_section.poles_var.append(pole_vm)

        # ✅ UI는 refresh에서 따로 그림
        self.refresh_poles()

    def refresh_poles(self):
        for w in self.winfo_children():
            w.destroy()

        headers = ["NO", '설치 레일', "전주 타입", '전주 규격', '전주 길이', '기초형식','건식게이지']
        for col, text in enumerate(headers):
            ttk.Label(self, text=text, font=("맑은 고딕", 9, "bold")).grid(row=0, column=col, padx=5, pady=2)

        for i, pole_vm in enumerate(self.current_section.poles_var, start=1):
            row = i
            ttk.Label(self, text=str(i)).grid(row=row, column=0)

            rail_labels = [rail.index for rail in self.current_section.rails_var]
            rail_uid_map = [rail.uid for rail in self.current_section.rails_var]

            # 🔥 디버그 출력
            print(f"[DEBUG] Pole {i}")
            print("  rail_labels:", rail_labels)
            print("  rail_uid_map:", rail_uid_map)
            print("  pole_vm.base_rail_uid:", pole_vm.base_rail_uid.get())
            print("  pole_vm.base_rail_index:", pole_vm.base_rail_index.get())

            base_rail_cb = ttk.Combobox(
                self,
                textvariable=pole_vm.base_rail_index,
                values=rail_labels,
                state="readonly",
                width=18
            )
            base_rail_cb.grid(row=row, column=1)
            base_rail_cb._pole_vm = pole_vm

            # ✅ 선택값 복원 시도
            uid = pole_vm.base_rail_uid.get()
            if uid in rail_uid_map:
                idx = rail_uid_map.index(uid)
                base_rail_cb.current(idx)
                pole_vm.base_rail_index.set(self.current_section.rails_var[idx].index_var.get())
                print(f"  -> matched uid {uid}, set combobox to index {idx}")
            else:
                base_rail_cb.set("")
                print(f"  -> uid {uid} not found in rail_uid_map")

            poletype_cb = ttk.Combobox(self, textvariable=pole_vm.poletype,
                         values=["강관주", "H형강주", "조립철주"],
                         state="readonly", width=15)
            poletype_cb.grid(row=row, column=2)

            polespeclist = {
                '강관주':["P10", "P12", "P14", "P16", "P18", "P20"],
                'H형강주':['H250x250','H300x300'],
                '조립철주':['L75x300x400','L75x450x450', 'L90x450x450']
            }
            # 전주 규격 콤보박스
            polespec_cb = ttk.Combobox(
                self,
                textvariable=pole_vm.polespec,
                values=polespeclist.get(pole_vm.poletype.get(), []),
                state="readonly",
                width=15
            )
            polespec_cb.grid(row=row, column=3)

            # 이벤트 바인딩: 타입 선택 시 규격 콤보박스 갱신 + 초기화
            def update_polespec(event, pole_vm=pole_vm, polespec_cb=polespec_cb):
                selected_type = pole_vm.poletype.get()
                values = polespeclist.get(selected_type, [])
                polespec_cb['values'] = values

                if values:
                    # ✅ 첫 번째 값으로 설정
                    polespec_cb.current(0)
                    pole_vm.polespec.set(values[0])
                else:
                    # 값이 없으면 초기화
                    pole_vm.polespec.set("")

            poletype_cb.bind("<<ComboboxSelected>>", update_polespec)

            # 기초형식 콤보박스
            polebaselist =['없음', '원형기초', '사각기초', '교량기초', '조립철주기초', '배수로기초', '옹벽기초']

            polebase_cb = ttk.Combobox(
                self,
                textvariable=pole_vm.foundation.basename_var,
                values=polebaselist,
                state="readonly",
                width=15
            )
            polebase_cb.grid(row=row, column=5)

            tk.Entry(self, textvariable=pole_vm.pole_length, width=6).grid(row=row, column=4)
            tk.Entry(self, textvariable=pole_vm.gauge, width=6).grid(row=row, column=6)

            self._bind_base_rail(base_rail_cb, pole_vm)

        self._refresh_pole_rail_combos()

    def _bind_base_rail(self, cb, pole_vm):
        def on_select(_):
            idx = cb.current()
            if idx >= 0:
                pole_vm.base_rail_uid.set(
                    self.current_section.rails_var[idx].uid
                )
                pole_vm.base_rail_index.set(self.current_section.rails_var[idx].index_var.get())

        cb.bind("<<ComboboxSelected>>", on_select)