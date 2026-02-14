from core.bracket.bracket_data import BracketDATA
from core.bracket.fitting_data import FittingDATA
from core.equipment.equipment_data import EquipmentDATA
from xref_module.object_libraymgr import LibraryManager
import tkinter as tk
from tkinter import ttk, messagebox
from xref_module.transaction import Transaction

class PoleAssemblerApp(tk.Toplevel):
    def __init__(self, runner, event= None):
        super().__init__()
        self.equip_combo = None
        self.epole = None
        self.title("전주 조립기")
        self.runner = runner
        self.event = event
        self.protocol("WM_DELETE_WINDOW", self.cancle)
        # event가 None일 수 있으므로 초기화 시점에는 바인딩하지 않음
        if self.event:
            self.bind_events()
        self.lib_manager = LibraryManager()  # 인스턴스 연결
        self.lib_manager.scan_library()  # 라이브러리 생성
        # 현재 선택 저장
        self.selection = {}
        #0 현재 전주 변수
        self.current_pole_var = tk.StringVar(value='현재 전주 없음')

        row = 0
        ttk.Label(self, text="현재 전주:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(self, textvariable=self.current_pole_var, state='readonly').grid(row=row, column=1, padx=5, pady=5)

        # 2. 위젯 생성
        # 전주 형식
        row += 1
        ttk.Label(self, text="전주 형식 선택:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.pole_var = tk.StringVar()
        self.pole_combo = ttk.Combobox(self, textvariable=self.pole_var, values=[], state="readonly")
        self.pole_combo.grid(row=row, column=1, padx=5, pady=5)

        # 브래킷
        row += 1
        ttk.Label(self, text="브래킷 종류:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.bracket_frame = ttk.Frame(self)
        self.bracket_frame.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        self.bracket_entries = []
        tk.Button(self, text="+브래킷", command=self.add_bracket_entry).grid(row=row, column=2, padx=5, pady=5)

        # 급전선
        row += 1
        self.feeder_vars = []
        ttk.Label(self, text="급전선 종류:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.feeder_var = tk.StringVar()
        self.feeder_xvar = tk.DoubleVar()
        self.feeder_yvar = tk.DoubleVar()
        self.feeder_rvar = tk.DoubleVar()
        feeders = self.lib_manager.list_files_in_category(category='급전선설비', group='base')
        self.feeder_combo = ttk.Combobox(self, textvariable=self.feeder_var,values=feeders, state="readonly")
        self.feeder_combo.grid(row=row, column=1, padx=5, pady=5)
        ttk.Entry(self, textvariable=self.feeder_xvar, width=5).grid(row=row, column=2, padx=5, pady=5)
        ttk.Entry(self, textvariable=self.feeder_yvar, width=5).grid(row=row, column=3, padx=5, pady=5)
        ttk.Entry(self, textvariable=self.feeder_rvar, width=5).grid(row=row, column=4, padx=5, pady=5)
        self.feeder_vars.append([self.feeder_var,self.feeder_xvar,self.feeder_yvar,self.feeder_rvar])
        # 보호선
        row += 1
        ttk.Label(self, text="보호선 지지물 종류:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.fpw_var = tk.StringVar()
        self.fpw_combo = ttk.Combobox(self, textvariable=self.fpw_var, state="disabled")
        self.fpw_combo.grid(row=row, column=1, padx=5, pady=5)

        # 추가 장비 영역
        row += 1
        ttk.Label(self, text="추가 장비:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.equip_frame = ttk.Frame(self)
        self.equip_frame.grid(row=row, column=1, padx=5, pady=5, sticky="w")

        self.equip_entries = []
        tk.Button(self, text="+", command=self.add_equip_entry).grid(row=row, column=2, padx=5, pady=5)

        # 건식게이지
        row += 1
        ttk.Label(self, text="건식게이지:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.gauge_var = tk.DoubleVar()
        self.gauge_combo = ttk.Combobox(self, textvariable=self.gauge_var)
        self.gauge_combo.grid(row=row, column=1, padx=5, pady=5)

        #버튼
        row += 1
        tk.Button(self, text="적용", command=self.apply_selection).grid(row=row, column=0, padx=5, pady=5, sticky="w")
        tk.Button(self, text="취소", command=self.cancle).grid(row=row, column=1, padx=5, pady=5, sticky="w")

    def add_equip_entry(self, name=None, offset=(0.0, 0.0), rotation=0.0):
        frame = ttk.Frame(self.equip_frame)
        frame.pack(fill="x", pady=2)

        eqs = self.lib_manager.list_all_files(group='base')
        equip_var = tk.StringVar(value=name if name else "")
        equip_combo = ttk.Combobox(frame, textvariable=equip_var,
                                   values=eqs, state="readonly")
        equip_combo.pack(side="left")

        offset_x = tk.DoubleVar(value=offset[0])
        offset_y = tk.DoubleVar(value=offset[1])
        rotation_var = tk.DoubleVar(value=rotation)
        ttk.Entry(frame, textvariable=offset_x, width=5).pack(side="left", padx=2)
        ttk.Entry(frame, textvariable=offset_y, width=5).pack(side="left", padx=2)
        ttk.Entry(frame, textvariable=rotation_var, width=5).pack(side="left", padx=2)

        remove_btn = tk.Button(frame, text="-", command=lambda: self.remove_equip_entry(frame))
        remove_btn.pack(side="left", padx=2)

        self.equip_entries.append((equip_var, offset_x, offset_y, rotation_var, frame))

    def remove_equip_entry(self, frame):
        for entry in self.equip_entries:
            if entry[3] == frame:
                self.equip_entries.remove(entry)
                break
        frame.destroy()

    def add_bracket_entry(self, name='', offset=(0.0, 0.0), rotation=0.0, fittings_data=None):
        frame = ttk.Frame(self.bracket_frame)
        frame.pack(fill="x", pady=2)

        # 선로 종류 선택
        railtype_var = tk.StringVar()
        railtype_combo = ttk.Combobox(
            frame,
            textvariable=railtype_var,
            values=['도시철도', '일반철도', '고속철도', '준고속철도'],
            state="readonly"
        )
        railtype_combo.pack(side="left")

        # 브래킷 선택
        bracket_var = tk.StringVar(value=name if name else "")
        bracket_combo = ttk.Combobox(frame, textvariable=bracket_var, values=[], state="readonly")
        bracket_combo.pack(side="left")

        def update_brackets(event=None):
            rail_type = railtype_var.get()
            if rail_type:
                group = self.lib_manager.define_group(rail_type)
                # 브래킷 목록 갱신
                brackets = self.lib_manager.list_files_in_category(category='브래킷', group=group)
                bracket_combo.config(values=brackets)
                # 피팅 목록 갱신

                for f_var, fx, fy, fr, f_frame in fittings:
                    # f_frame 안의 콤보박스 찾아서 갱신
                    for child in f_frame.winfo_children():
                        if isinstance(child, ttk.Combobox):
                            child.config(values=brackets)

        railtype_combo.bind("<<ComboboxSelected>>", update_brackets)

        # offset, rotation 입력
        offset_x = tk.DoubleVar(value=offset[0])
        offset_y = tk.DoubleVar(value=offset[1])
        rotation_var = tk.DoubleVar(value=rotation)
        ttk.Entry(frame, textvariable=offset_x, width=5).pack(side="left", padx=2)
        ttk.Entry(frame, textvariable=offset_y, width=5).pack(side="left", padx=2)
        ttk.Entry(frame, textvariable=rotation_var, width=5).pack(side="left", padx=2)

        # 피팅 영역
        fitting_frame = ttk.Frame(frame)
        fitting_frame.pack(side="left", padx=5)
        fittings = []

        def add_fitting_entry(name='', offset=(0.0, 0.0), rotation=0.0):
            f_frame = ttk.Frame(fitting_frame)
            f_frame.pack(fill="x", pady=1)

            f_var = tk.StringVar(value=name)
            rail_type = railtype_var.get()
            group = self.lib_manager.define_group(rail_type) if rail_type else 'base'
            f_combo = ttk.Combobox(f_frame, textvariable=f_var,
                                   values=self.lib_manager.list_files_in_category('브래킷', group=group),
                                   state="readonly")
            f_combo.pack(side="left")

            fx = tk.DoubleVar(value=offset[0])
            fy = tk.DoubleVar(value=offset[1])
            fr = tk.DoubleVar(value=rotation)
            ttk.Entry(f_frame, textvariable=fx, width=5).pack(side="left")
            ttk.Entry(f_frame, textvariable=fy, width=5).pack(side="left")
            ttk.Entry(f_frame, textvariable=fr, width=5).pack(side="left")

            tk.Button(f_frame, text="-피팅", command=lambda: remove_fitting_entry(f_frame)).pack(side="left")

            fittings.append((f_var, fx, fy, fr, f_frame))

        def remove_fitting_entry(f_frame):
            for f in fittings:
                if f[4] == f_frame:
                    fittings.remove(f)
                    break
            f_frame.destroy()

        tk.Button(frame, text="+피팅", command=lambda: add_fitting_entry()).pack(side="left")

        # 삭제 버튼
        remove_btn = tk.Button(frame, text="-브래킷", command=lambda: self.remove_bracket_entry(frame))
        remove_btn.pack(side="left", padx=2)

        entry = {
            "bracket_var": bracket_var,
            "offset_x": offset_x,
            "offset_y": offset_y,
            "rotation_var": rotation_var,
            "frame": frame,
            "fittings": fittings
        }

        self.bracket_entries.append(entry)

        # 기존 피팅 데이터 복원
        if fittings_data:
            for f in fittings_data:
                add_fitting_entry(name=f.label, offset=f.offset, rotation=f.rotation)

    def remove_bracket_entry(self, frame):
        for entry in self.equip_entries:
            if entry[3] == frame:
                self.equip_entries.remove(entry)
                break
        frame.destroy()


    # 초기화 이후에도 호출 가능
    def bind_events(self):
        self.event.bind("pole_selected", self.on_pole_selected)

    def on_pole_selected(self, epole):
        if not self.winfo_exists():
            return

        self.epole = epole
        if self.epole is not None:
            self.current_pole_var.set(str(self.epole.pole.post_number))

            # 기존 엔트리 제거
            for _, _, _, _, frame in self.equip_entries:
                frame.destroy()
            self.equip_entries.clear()

            for entry in self.bracket_entries:
                for f_var, fx, fy, fr, f_frame in entry["fittings"]:
                    f_frame.destroy()
                entry["fittings"].clear()
                entry["frame"].destroy()
            self.bracket_entries.clear()

            # 속성 복원
            self.pole_var.set(self.epole.pole.mast.name)
            for br in self.epole.pole.brackets:
                self.add_bracket_entry(name=br.bracket_name,
                                       offset=br.offset,
                                       rotation=br.rotation,
                                       fittings_data=br.fittings)

            for equip in self.epole.pole.equipments:
                if equip.type == '급전선설비':
                    self.feeder_vars.clear()
                    self.feeder_var.set(equip.name)
                    self.feeder_xvar.set(equip.offset[0])
                    self.feeder_yvar.set(equip.offset[1])
                    self.feeder_rvar.set(equip.rotation)
                    self.feeder_vars.append([self.feeder_var, self.feeder_xvar, self.feeder_yvar, self.feeder_rvar])
                else:
                    self.add_equip_entry(name=equip.name,
                                         offset=equip.offset,
                                         rotation=equip.rotation)

            self.gauge_var.set(self.epole.pole.gauge)

    def apply_selection(self):
        self.selection["pole"] = self.pole_var.get()
        self.selection["brackets"] = self.bracket_entries
        self.selection["feeder"] = self.feeder_vars
        self.selection["fpw"] = self.fpw_var.get()
        self.selection["equipments"] = self.equip_entries
        self.selection["gauge"] = self.gauge_var.get()
        self.commit_to_poledata()
        self.event.emit('pole_modified')

    def commit_to_poledata(self):
        try:
            if self.epole is None:
                messagebox.showerror('에러', '전주가 선택되지 않았습니다. 먼저 전주를 선택하세요')
                return
            pole = self.epole.pole
            if pole.section is not None:
                messagebox.showerror('에러', '일반구간만 편집이 가능합니다. 다른 전주를 선택하세요')
                return
            with Transaction(pole):
                # 건식게이지 적용
                pole.gauge = self.selection["gauge"]
                #전주 적용
                mast_name = self.selection["pole"].replace('.csv','')
                pole.mast.name = mast_name
                pole.mast.index = self.runner.idxlib.get_index(mast_name)
                pole.mast.offset = self.selection["gauge"]
                #브래킷 적용
                pole.brackets.clear()
                for br in self.selection["brackets"]:
                    bracket_name = br['bracket_var'].get().replace('.csv','')
                    index = self.runner.idxlib.get_index(bracket_name)
                    offset = br['offset_x'].get(), br['offset_y'].get()
                    rotation = br['rotation_var'].get()
                    bracket = BracketDATA(
                        bracket_type=pole.base_type,
                        index=index,
                        offset=offset,
                        rotation=rotation,
                        bracket_name=bracket_name
                    )
                    for fit in br["fittings"]:
                        name = fit[0].get().replace('.csv','')
                        index = self.runner.idxlib.get_index(name)
                        offset = fit[1].get(), fit[2].get()
                        rotation = fit[3].get()
                        fitting = FittingDATA(index, offset, rotation, name)
                        bracket.fittings.append(fitting)
                    pole.brackets.append(bracket)
                #급전선 장비 적용
                pole.equipments.clear()
                if self.selection["feeder"]:
                    feeder_name = self.selection["feeder"][0][0].get().replace('.csv','')
                    feeder_idx =  self.runner.idxlib.get_index(feeder_name)
                    feeder_xoffset = self.selection["feeder"][0][1].get()
                    feeder_yoffset = self.selection["feeder"][0][2].get()
                    feeder_roffset = self.selection["feeder"][0][3].get()
                    pole.equipments.append(EquipmentDATA(name=feeder_name,index=feeder_idx,offset=(feeder_xoffset,feeder_yoffset),rotation=feeder_roffset,type='급전선설비'))

                #보호선 금구 적용
                if self.selection["fpw"] != '':
                    fpw_name = self.selection["fpw"].replace('.csv','')
                    fpw_idx = self.runner.idxlib.get_index(fpw_name)
                    pole.equipments.append(EquipmentDATA(name=fpw_name, index=fpw_idx,type='보호선설비'))

                #추가장비 적용
                for equipment in self.selection["equipments"]:
                    etc_name = equipment[0].get().replace('.csv','')
                    etc_idx = self.runner.idxlib.get_index(etc_name)
                    x = equipment[1].get()
                    y = equipment[2].get()
                    r = equipment[3].get()
                    pole.equipments.append(EquipmentDATA(name=etc_name, index=etc_idx, offset=(x,y), rotation=r,type='기타장비'))


                self.runner.log(f'{pole.post_number}: 전주 편집 성공! 장비가 성공적으로 적용됐습니다.')

        except Exception as e:
            messagebox.showerror('에러', f'전주 편집에 실패했습니다. {e}')
            return

    def cancle(self):
        if self.event:
            self.event.unbind("pole_selected", self.on_pole_selected)
        self.destroy()