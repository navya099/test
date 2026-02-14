import tkinter as tk
from tkinter import ttk, messagebox

from gui.pole_assembler import PoleAssemblerApp
from gui.wireeditor import WireEditor
from vms.editable_pole import EditablePole
from vms.editable_wires import EditableWire
from vms.eidtable_bracket import BracketEditor
from xref_module.transaction import Transaction


class AutoPoleEditor(tk.Frame):
    def __init__(self, runner, events=None, master=None):
        super().__init__(master)
        self.runner = runner
        self.events = events
        self.editable_poles = {"main": [], "sub": []}
        self.editable_wires = {"main": [], "sub": []}

        # 이벤트 바인딩
        if self.events:
            self.events.bind('pole_moved', self.on_pole_moved)
            self.events.bind('pole_modified', self.on_pole_modifeyed)

        # Notebook 생성 (본선/상선 탭)
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # 본선 탭
        frame_main = tk.Frame(notebook)
        notebook.add(frame_main, text="본선")
        self.tree_main = ttk.Treeview(
            frame_main,
            columns=("전주번호", "측점", '경간', "건식게이지", "구조물", "구간",
                     "기본 타입", '곡선반경', '구배', '캔트', '계획고'),
            show="headings"
        )
        self.tree_main.pack(fill="both", expand=True)
        for col in ("전주번호", "측점", '경간', "건식게이지", "구조물", "구간",
                    "기본 타입", '곡선반경', '구배', '캔트', '계획고'):
            self.tree_main.heading(col, text=col)
            self.tree_main.column(col, width=100, anchor="center")

        # 상선 탭
        frame_sub = tk.Frame(notebook)
        notebook.add(frame_sub, text="상선")
        self.tree_sub = ttk.Treeview(
            frame_sub,
            columns=("전주번호", "측점", '경간', "건식게이지", "구조물", "구간",
                     "기본 타입", '곡선반경', '구배', '캔트', '계획고'),
            show="headings"
        )
        self.tree_sub.pack(fill="both", expand=True)
        for col in ("전주번호", "측점", '경간', "건식게이지", "구조물", "구간",
                    "기본 타입", '곡선반경', '구배', '캔트', '계획고'):
            self.tree_sub.heading(col, text=col)
            self.tree_sub.column(col, width=100, anchor="center")

        # 데이터 로딩
        self.load_data()

        # Entry + 버튼 영역 (공통)
        frame_controls = tk.Frame(self)
        frame_controls.pack(fill="x", pady=5)

        tk.Label(frame_controls, text="전주번호").pack(side="left")
        self.entry_post_number = tk.Entry(frame_controls, width=10)
        self.entry_post_number.pack(side="left")

        tk.Label(frame_controls, text="측점").pack(side="left")
        self.entry_pos = tk.Entry(frame_controls, width=10)
        self.entry_pos.pack(side="left")

        tk.Label(frame_controls, text="건식게이지").pack(side="left")
        self.entry_gauge = tk.Entry(frame_controls, width=10)
        self.entry_gauge.pack(side="left")

        tk.Label(frame_controls, text="구조물").pack(side="left")
        self.entry_structure = tk.Entry(frame_controls, width=10)
        self.entry_structure.pack(side="left")

        tk.Label(frame_controls, text="구간").pack(side="left")
        self.entry_section = tk.Entry(frame_controls, width=10)
        self.entry_section.pack(side="left")

        tk.Label(frame_controls, text="기본 타입").pack(side="left")
        self.entry_base_type = tk.Entry(frame_controls, width=10)
        self.entry_base_type.pack(side="left")

        # 버튼
        tk.Button(self, text="선택 불러오기", command=self.load_selected).pack()
        tk.Button(self, text="수정 저장", command=self.save_edit).pack()
        tk.Button(self, text="전주 상세 편집", command=self.open_equipment_editor).pack()
        tk.Button(self, text="전선 상세 편집", command=self.open_wire_editor).pack()



    def load_data(self):
        if not self.runner.poledata:
            print("poledata가 아직 초기화되지 않았습니다.")
            return

        # 본선 데이터 로딩

        for pole in self.runner.poledata.get("main", []):
            self.tree_main.insert("", "end", values=(
                pole.post_number, pole.pos, pole.span, pole.gauge,
                pole.structure, pole.section, pole.base_type,
                pole.radius, pole.pitch, pole.cant, pole.z
            ))

        # 상선 데이터 로딩
        for pole in self.runner.poledata.get("sub", []):
            self.tree_sub.insert("", "end", values=(
                pole.post_number, pole.pos, pole.span, pole.gauge,
                pole.structure, pole.section, pole.base_type,
                pole.radius, pole.pitch, pole.cant, pole.z
            ))


    def on_pole_moved(self):
        self.refresh_tree()

    def on_pole_modifeyed(self):
        self.refresh_tree()

    def refresh_tree(self):
        if not self.runner.poledata:
            return

        # 본선 트리 초기화
        for row in self.tree_main.get_children():
            self.tree_main.delete(row)
        for pole in self.runner.poledata.get("main", []):
            self.tree_main.insert("", "end", values=(
                pole.post_number, pole.pos, pole.span, pole.gauge,
                pole.structure, pole.section, pole.base_type,
                pole.radius, pole.pitch, pole.cant, pole.z
            ))

        # 상선 트리 초기화
        for row in self.tree_sub.get_children():
            self.tree_sub.delete(row)
        for pole in self.runner.poledata.get("sub", []):
            self.tree_sub.insert("", "end", values=(
                pole.post_number, pole.pos, pole.span, pole.gauge,
                pole.structure, pole.section, pole.base_type,
                pole.radius, pole.pitch, pole.cant, pole.z
            ))

    def load_selected(self):
        # 본선 탭에서 선택
        selected_main = self.tree_main.selection()
        if selected_main:
            item = self.tree_main.item(selected_main[0])
            self._handle_selection(item, track="main")

        # 상선 탭에서 선택
        selected_sub = self.tree_sub.selection()
        if selected_sub:
            item = self.tree_sub.item(selected_sub[0])
            self._handle_selection(item, track="sub")

    def _handle_selection(self, item, track):
        post_number, pos, span, gauge, structure, section, base_type, radius, pitch, cant, z = item["values"]

        # epole 객체 찾기
        epole = None
        for e in self.editable_poles.get(track, []):
            if e.pole.pos == pos:
                epole = e
                break

        # ewire 객체 찾기
        ewire = None
        for w in self.editable_wires.get(track, []):
            if w.wire.pos == pos:
                ewire = w
                break

        # 이벤트 발행
        if self.events:
            if epole is not None:
                self.events.emit("pole_selected", epole)
            if ewire is not None:
                self.events.emit("wire_selected", ewire)

        # Entry 채우기
        self.original_pos = pos
        self.entry_post_number.delete(0, tk.END)
        self.entry_post_number.insert(0, post_number)
        self.entry_pos.delete(0, tk.END)
        self.entry_pos.insert(0, pos)
        self.entry_gauge.delete(0, tk.END)
        self.entry_gauge.insert(0, gauge)
        self.entry_structure.delete(0, tk.END)
        self.entry_structure.insert(0, structure)
        self.entry_section.delete(0, tk.END)
        self.entry_section.insert(0, section)
        self.entry_base_type.delete(0, tk.END)
        self.entry_base_type.insert(0, base_type)

    def create_epoles(self):
        # EditablePole 리스트 생성
        self.editable_poles = {"main": [], "sub": []}

        for track_name, poles in self.runner.poledata.items():
            prev_epole = None
            for pole in poles:
                epole = EditablePole(
                    pole,
                    self.runner.structure_list,
                    self.runner.curvelist,
                    self.runner.pitchlist,
                    self.runner.polyline_with_sta if track_name == "main" else self.runner.offset_line_with_25,
                    prev_pole=prev_epole
                )
                self.editable_poles[track_name].append(epole)
                if prev_epole:
                    prev_epole.next_pole = epole
                prev_epole = epole

    def create_ewires(self):
        # EditableWire 리스트 생성
        self.editable_wires = {"main": [], "sub": []}

        for track_name, wires in self.runner.wire_data.items():
            prev_ewire = None
            for wire in wires:
                ewire = EditableWire(
                    wire,
                    self.runner.structure_list,
                    self.runner.curvelist,
                    self.runner.pitchlist,
                    self.runner.polyline_with_sta if track_name == "main" else self.runner.offset_line_with_25,
                    prev_wire=prev_ewire
                )
                self.editable_wires[track_name].append(ewire)
                if prev_ewire:
                    prev_ewire.next_wire = ewire
                prev_ewire = ewire

    def save_edit(self):
        new_post_number = self.entry_post_number.get()
        new_pos = int(self.entry_pos.get())
        new_gauge = float(self.entry_gauge.get())
        new_section = self.entry_section.get() if self.entry_section.get() != 'None' else None
        new_base_type = self.entry_base_type.get()

        found = False
        for track_name, poles in self.editable_poles.items():
            for epole in poles:
                if epole.pole.pos == self.original_pos:
                    found = True
                    try:
                        # 일반개소만 편집 허용
                        if epole.pole.section is not None:
                            messagebox.showerror('전주 업데이트 실패', f'지정한 {epole.pole.pos}는 일반 개소가 아닙니다.')
                            return

                        # 새 span 계산
                        new_span = epole.pole.next_pos - new_pos
                        if new_span not in self.runner.dataprocessor.get_span_list():
                            messagebox.showerror('전주 업데이트 실패', f'경간 {new_span}은 지정된 spanlist에 없습니다.')
                            return

                        with Transaction(epole.pole, epole.prev_pole.pole, epole.next_pole.pole):
                            epole.update(
                                post_number=new_post_number,
                                pos=new_pos,
                                gauge=new_gauge,
                                section=new_section,
                                base_type=new_base_type
                            )
                            BracketEditor.update(epole.pole, self.runner.dataprocessor, self.runner.idxlib)
                        break
                    except Exception as e:
                        messagebox.showerror('전주 업데이트 실패', str(e))
                        return
            if found:
                break

        # radius, cant, pitch, z, span, next_pos 등은 자동 재계산 예정
        self.refresh_tree()
        # 와이어 전체 재계산
        self.runner.wire_data = self.runner.wire_processor.process_to_wire()

        if self.events:
            self.events.emit("pole_saved")

        self.runner.log(f'전주 편집 성공 {new_pos}')

    def open_equipment_editor(self):
        asemlbapp = PoleAssemblerApp(self.runner, self.events)
        asemlbapp.bind_events()

    def open_wire_editor(self):
        we = WireEditor(self.runner, self.events)
        we.bind_events()