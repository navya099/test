from gui.viewmodel.beam_vm import BeamVM
from gui.viewmodel.bracket_input import BracketViewModel
from gui.viewmodel.pole_vm import PoleVM
from gui.viewmodel.polebasevm import PoleBaseVM
from gui.viewmodel.tkinstalldata import TKInstallData
from model.tkraildata import TKRailData
from alignment_geometry.alignment_interpolator import RailInterpolator


import tkinter as tk
from tkinter import ttk, messagebox

class AutoDesignManager:
    def __init__(self, section_frame):
        self.sf = section_frame
        self.sub_line = section_frame.sub_line

    def run(self, start_sta, length, span):
        if not self.sub_line:
            messagebox.showwarning("경고", "선로 데이터가 없습니다.")
            return

        end_sta = start_sta + length
        current_sta = start_sta
        new_sections = []

        while current_sta <= end_sta:
            # 1. 측점별 선로 보간
            valid_rails_info = []
            for al in self.sub_line:
                pos = RailInterpolator.get_point_at_station(current_sta, al.raildata)
                if pos:
                    valid_rails_info.append({'idx': al.index, 'name': al.name, 'x': pos[0], 'y': pos[1]})

            if not valid_rails_info:
                current_sta += span
                continue

            # 2. 최외곽 선로 식별
            valid_rails_info.sort(key=lambda r: r['x'])
            left_info = valid_rails_info[0]
            right_info = valid_rails_info[-1]

            # 3. 메인 설치 데이터 생성
            new_install = TKInstallData(
                station_var=tk.DoubleVar(value=current_sta),
                pole_number_var=tk.StringVar(value=f"P-{int(current_sta)}"),
                rail_count_var=tk.IntVar(value=len(valid_rails_info)),
                pole_count_var=tk.IntVar(value=2),
                beam_count_var=tk.IntVar(value=1),
                isbeaminstall_var=tk.BooleanVar(value=True),
                iid='',
                beams_var = [],
                poles_var = [],
                rails_var = [],
                equips_var = [],
                wires_var = []
            )

            # 4. 레일 데이터 생성 및 최외곽 매칭
            left_tkrail = None
            right_tkrail = None

            for r in valid_rails_info:
                rail_obj = TKRailData(
                    index_var=tk.IntVar(value=r['idx']),
                    name_var=tk.StringVar(value=r['name']),
                    brackets=[BracketViewModel(
                        rail_no=tk.IntVar(value=r['idx']),
                        bracket_type=tk.StringVar(value='G2.1-I'),
                        xoffset=tk.DoubleVar(value=0.0),
                        yoffset=tk.DoubleVar(value=0.0),
                        rotation=tk.DoubleVar(value=0.0),
                        rail_type=tk.StringVar(value='일반철도'),
                        fittings=[]
                        )
                    ],
                    coordx=tk.DoubleVar(value=r['x']),
                    coordy=tk.DoubleVar(value=r['y']),
                    coordz=tk.DoubleVar(value=0.0)
                )
                new_install.rails_var.append(rail_obj)

                # 인덱스 비교로 최외곽 레일 객체 보관
                if r['idx'] == left_info['idx']: left_tkrail = rail_obj
                if r['idx'] == right_info['idx']: right_tkrail = rail_obj

            # 5. 전주(Pole) 생성 및 최외곽 레일 연결
            # Gauge: 좌측은 마이너스(-3.5), 우측은 플러스(3.5)로 설정
            lp_vm = PoleVM(
                index=tk.IntVar(value=0),
                poletype=tk.StringVar(value="강관주"),
                polespec=tk.StringVar(value="P12"),
                pole_length=tk.DoubleVar(value=9.0),
                base_rail_index=tk.IntVar(value=left_info['idx']),
                base_rail_uid=tk.StringVar(value=left_tkrail.uid),
                gauge=tk.DoubleVar(value=-3.5),
                foundation=PoleBaseVM(basename_var=tk.StringVar(value='')),
            )
            rp_vm = PoleVM(
                index=tk.IntVar(value=1),
                poletype=tk.StringVar(value="강관주"),
                polespec=tk.StringVar(value="P12"),
                pole_length=tk.DoubleVar(value=9.0),
                base_rail_index=tk.IntVar(value=right_info['idx']),
                base_rail_uid=tk.StringVar(value=right_tkrail.uid),
                gauge=tk.DoubleVar(value=3.5),  # 우측은 양수값
                foundation=PoleBaseVM(basename_var=tk.StringVar(value='')),
            )
            new_install.poles_var = [lp_vm, rp_vm]

            # 6. 빔(Beam) 생성 및 연결
            beam_vm = BeamVM(
                index=tk.IntVar(value=0),
                beamtype=tk.StringVar(value="트러스빔"),
                start_pole=lp_vm.index,  # 인덱스 객체 전달
                end_pole=rp_vm.index
            )
            new_install.beams_var = [beam_vm]

            new_sections.append(new_install)
            current_sta += span

        self._apply_to_ui(new_sections)

    def _apply_to_ui(self, new_sections):
        """기존 SectionFrame의 Treeview와 리스트를 갱신"""
        # 기존 데이터 삭제 여부 확인
        if messagebox.askyesno("확인", "기존 구간 데이터를 삭제하고 자동 설계를 적용할까요?"):
            self.sf.sections.clear()
            self.sf.section_list.delete(*self.sf.section_list.get_children())
            self.sf.section_map.clear()

        for section in new_sections:
            iid = self.sf.section_list.insert("", "end", values=(
                section.station_var.get(),
                section.pole_number_var.get()
            ))
            section.iid = iid
            self.sf.section_map[iid] = section
            self.sf.sections.append(section)

        messagebox.showinfo("완료", f"{len(new_sections)}개 구간 자동 설계 완료")



class AutoDesignDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("정거장 일괄 자동 설계")
        self.geometry("300x200")
        self.result = None

        # 입력 필드 레이아웃
        fields = [("시작 측점 (m):", "start", "0"),
                  ("설계 길이 (m):", "length", "300"),
                  ("표준 경간 (m):", "span", "50")]

        self.entries = {}
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, padx=10, pady=5)
            ent = ttk.Entry(self)
            ent.insert(0, default)
            ent.grid(row=i, column=1, padx=10, pady=5)
            self.entries[key] = ent

        ttk.Button(self, text="설계 시작", command=self.on_apply).grid(row=3, columnspan=2, pady=10)

    def on_apply(self):
        try:
            self.result = {
                "start": float(self.entries["start"].get()),
                "length": float(self.entries["length"].get()),
                "span": float(self.entries["span"].get())
            }
            self.destroy()
        except ValueError:
            messagebox.showerror("에러", "숫자만 입력해주세요.")