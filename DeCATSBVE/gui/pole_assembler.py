from core.equipment.equipment_data import EquipmentDATA
from core.mast.mastdata import Mast
from xref_module.object_libraymgr import LibraryManager
import tkinter as tk
from tkinter import ttk, messagebox

from xref_module.transaction import Transaction


class PoleAssemblerApp(tk.Toplevel):
    def __init__(self, runner, event= None):
        super().__init__()
        self.epole = None
        self.title("전주 조립기")
        self.runner = runner
        self.event = event
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

        # 1. 선로 종류 선택
        row += 1
        ttk.Label(self, text="선로 종류 선택:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.railtype_var = tk.StringVar()
        self.railtype_combo = ttk.Combobox(
            self,
            textvariable=self.railtype_var,
            values=['도시철도', '일반철도', '고속철도', '준고속철도'],
            state="readonly"
        )
        self.railtype_combo.grid(row=row, column=1, padx=5, pady=5)
        self.railtype_combo.bind("<<ComboboxSelected>>", self.update_options)

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
        self.bracket_var = tk.StringVar()
        self.bracket_combo = ttk.Combobox(self, textvariable=self.bracket_var, state="disabled")
        self.bracket_combo.grid(row=row, column=1, padx=5, pady=5)

        # 급전선
        row += 1
        ttk.Label(self, text="급전선 종류:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.feeder_var = tk.StringVar()
        self.feeder_combo = ttk.Combobox(self, textvariable=self.feeder_var, state="disabled")
        self.feeder_combo.grid(row=row, column=1, padx=5, pady=5)

        # 보호선
        row += 1
        ttk.Label(self, text="보호선 지지물 종류:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.fpw_var = tk.StringVar()
        self.fpw_combo = ttk.Combobox(self, textvariable=self.fpw_var, state="disabled")
        self.fpw_combo.grid(row=row, column=1, padx=5, pady=5)

        # 추가장비
        row += 1
        ttk.Label(self, text="추가 장비:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.equip_var = tk.StringVar()
        self.equip_cb = ttk.Combobox(self, textvariable=self.equip_var, state="disabled")
        self.equip_cb.grid(row=row, column=1, padx=5, pady=5)

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


    # 초기화 이후에도 호출 가능
    def bind_events(self):
        self.event.bind("pole_selected", self.on_pole_selected)

    # 전주 선택 시 옵션 업데이트
    def update_options(self, event):
        """
        콤보상자 옵션 업데이트 메소드
        :param event:
        :return:
        """
        rail_type = self.railtype_var.get()
        group = self.lib_manager.define_group(rail_type)

        # 전주 목록 조회
        poles = self.lib_manager.list_files_in_category('기둥', group='base')

        self.pole_combo.config(values=poles)

        # 브래킷 리스트 가져오기
        brackets = self.lib_manager.list_files_in_category(category='브래킷', group=group)
        self.bracket_combo.config(values=brackets, state="readonly")

        # 급전선 세팅
        feeders = self.lib_manager.list_files_in_category(category='급전선설비', group='base')
        self.feeder_combo.config(values=feeders, state="readonly")

        # 보호선 세팅
        fpws = self.lib_manager.list_files_in_category(category='금구류', group='base')
        self.fpw_combo.config(values=fpws, state="readonly")

        #추가 장비 세팅
        eqs = self.lib_manager.list_all_files(group='base')
        self.equip_cb.config(values=eqs, state="readonly")

    def on_pole_selected(self, epole):
        print('디버그 전주 수신됨')
        self.epole = epole
        if self.epole is not None:
            self.current_pole_var.set(str(self.epole.pole.post_number))

    def apply_selection(self):
        self.selection["pole"] = self.pole_var.get()
        self.selection["bracket"] = self.bracket_var.get()
        self.selection["feeder"] = self.feeder_var.get()
        self.selection["fpw"] = self.fpw_var.get()
        self.selection["equipment"] = self.equip_var.get()
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

                #전주 적용
                mast_name = self.selection["pole"].replace('.csv','')
                pole.mast.name = mast_name
                pole.mast.index = self.runner.idxlib.get_index(mast_name)
                pole.mast.offset = self.selection["gauge"]
                #브래킷 적용
                bracket_name = self.selection["bracket"].replace('.csv','')
                pole.brackets[0].bracket_type = bracket_name
                pole.brackets[0].index = self.runner.idxlib.get_index(bracket_name)
                pole.brackets[0].bracket_name = self.selection["bracket"]

                #급전선 장비 적용
                pole.equipments.clear()
                feeder_name = self.selection["feeder"].replace('.csv','')
                feeder_idx =  self.runner.idxlib.get_index(feeder_name)
                pole.equipments.append(EquipmentDATA(name=feeder_name,index=feeder_idx))

                #보호선 금구 적용
                fpw_name = self.selection["fpw"].replace('.csv','')
                fpw_idx = self.runner.idxlib.get_index(fpw_name)
                pole.equipments.append(EquipmentDATA(name=fpw_name, index=fpw_idx))

                #추가장비 적용
                etc_name = self.selection["equipment"].replace('.csv','')
                etc_idx = self.runner.idxlib.get_index(etc_name)
                pole.equipments.append(EquipmentDATA(name=etc_name, index=etc_idx))

                #건식게이지 적용
                pole.gauge = self.selection["gauge"]
                self.runner.log(f'{pole.post_number}: 전주 편집 성공! 장비가 성공적으로 적용됐습니다.')

        except Exception as e:
            messagebox.showerror('에러', f'전주 편집에 실패했습니다. {e}')
            return

    def cancle(self):
        self.destroy()