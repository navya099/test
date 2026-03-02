from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
from gui.viewmodel.tkinstalldata import TKInstallData


class SectionFrame(ttk.LabelFrame):
    def __init__(self, master, event=None):
        super().__init__(master, text="구간 정보")
        self.main_line = None
        self.sub_line = None
        self.section_map = {}
        self.selected_items = None
        self.event = event
        if self.event:
            self.event.bind("basic.changed", self.on_basic_changed)
            self.event.bind('station.loaded', self.on_station_loaded)
        self.section_list = None #TK트리뷰 리스트
        self.sections = [] #TK 뷰 모델 데이터 리스트
        self.selected_object = None #선택한 섹션 객체
        self._build()

    def on_station_loaded(self, als):
        self.main_line = als[0]
        self.sub_line = als[1]

    def _build(self):
        # Treeview 생성
        self.section_list = ttk.Treeview(
            self,
            columns=("station", "pole_number"),
            show="headings",
            height=8
        )
        self.section_list.heading("station", text="측점")
        self.section_list.heading("pole_number", text="전주번호")
        self.section_list.pack(fill="x", padx=10, pady=5)

        # ✅ 선택 이벤트 바인딩
        self.section_list.bind("<<TreeviewSelect>>", self._on_treeview_select)

        # 버튼 프레임
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="구간 추가", command=self.add_section).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="구간 삭제", command=self.remove_section).pack(side="left", padx=5)
        # "구간 선택" 버튼은 필요 없음
    def add_section(self):
        if not self.sub_line and not self.main_line:
            messagebox.showerror('에러', '로드된 정거장정보가 없습니다. 먼저 정거장파일을 불러와주세요' )
            return

        new_install = TKInstallData(
            station_var=tk.DoubleVar(value=0.0),
            pole_number_var=tk.StringVar(value='새 전주'),
            rail_count_var=tk.IntVar(value=len(self.sub_line)),
            pole_count_var=tk.IntVar(value=0),
            beam_count_var=tk.IntVar(value=0),
            poles_var=[],
            beams_var=[],
            rails_var=[],
            equips_var =[],
            wires_var=[],
            isbeaminstall_var=tk.BooleanVar(value=True),
            iid='')

        # Treeview에 추가하고 iid를 받아옴
        iid = self.section_list.insert("", "end",
                                       values=(new_install.station_var.get(),
                                               new_install.pole_number_var.get()))
        new_install.iid = iid
        # 매핑 저장
        self.section_list.set(iid, "station", new_install.station_var.get())
        self.section_list.set(iid, "pole_number", new_install.pole_number_var.get())

        # 객체를 딕셔너리에 저장
        if not hasattr(self, "section_map"):
            self.section_map = {}
        self.section_map[iid] = new_install
        self.sections.append(new_install)
        if self.event:
            self.event.emit("section.added", new_install)

    def remove_section(self):
        selected_items = self.section_list.selection()
        for item in selected_items:
            # 삭제 전에 값 가져오기
            values = self.section_list.item(item, "values")

            # 내부 리스트에서 제거
            if hasattr(self, "sections"):
                self.sections = [
                    s for s in self.sections
                    if not (s.station_var.get() == float(values[0]) and
                            s.pole_number_var.get() == values[1])
                ]

            # Treeview에서 삭제
            self.section_list.delete(item)

        if self.event:
            self.event.emit("section.removed", selected_items)

    def _on_treeview_select(self, event=None):
        selected_items = self.section_list.selection()
        if not selected_items:
            return

        iid = selected_items[0]
        self.selected_object = self.section_map.get(iid)

        if self.event and self.selected_object:
            self.event.emit("section.selected", self.selected_object)

    def on_basic_changed(self, section):
        # 선택된 구간의 값이 바뀌었을 때 Treeview 갱신
        self.update_treeview(section)

    def update_treeview(self, section):
        # section 객체를 찾아서 Treeview 값 갱신
        for iid, obj in self.section_map.items():
            if obj is section:
                self.section_list.item(iid,
                                       values=(section.station_var.get(), section.pole_number_var.get()))
                break

    def refresh_sections(self):
        # 기존 구간 초기화
        self.section_list.delete(*self.section_list.get_children())
        self.section_map.clear()

        # VM 리스트를 다시 Treeview에 반영
        for section in self.sections:
            iid = self.section_list.insert(
                "", "end",
                values=(section.station_var.get(), section.pole_number_var.get())
            )
            section.iid = iid
            self.section_map[iid] = section