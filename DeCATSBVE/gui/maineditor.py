import tkinter as tk
from tkinter import ttk, messagebox

from gui.pole_assembler import PoleAssemblerApp
from vms.editable_pole import EditablePole
from vms.eidtable_bracket import BracketEditor
from xref_module.transaction import Transaction


class AutoPoleEditor(tk.Frame):
    def __init__(self, runner, events=None, master=None):
        super().__init__(master)
        self.runner = runner
        self.events = events
        if self.events:
            # pole_moved 이벤트가 발생하면 on_pole_moved 실행
            self.events.bind('pole_moved', self.on_pole_moved)
            self.events.bind('pole_modified', self.on_pole_modifeyed)

        self.editable_poles = []

        # Treeview + Scrollbar 프레임
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)

        # Treeview 생성
        self.tree = ttk.Treeview(
            frame,
            columns=("전주번호", "측점", '경간', "건식게이지", "구조물", "구간", "기본 타입", '곡선반경','구배','캔트','계획고'),
            show="headings"
        )
        for col in ("전주번호", "측점", '경간', "건식게이지", "구조물", "구간", "기본 타입", '곡선반경','구배','캔트','계획고'):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")  # 기본 폭 지정

        # 가로 스크롤바 추가
        xscroll = tk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=xscroll.set)

        # 배치
        self.tree.pack(side="top", fill="both", expand=True)
        xscroll.pack(side="bottom", fill="x")

        # Entry widgets + Label
        frame_post_number = tk.Frame(self)
        tk.Label(frame_post_number, text="전주번호").pack(side="left")
        self.entry_post_number = tk.Entry(frame_post_number)
        self.entry_post_number.pack(side="left")
        frame_post_number.pack()

        frame_pos = tk.Frame(self)
        tk.Label(frame_pos, text="측점").pack(side="left")
        self.entry_pos = tk.Entry(frame_pos)
        self.entry_pos.pack(side="left")
        frame_pos.pack()

        frame_gauge = tk.Frame(self)
        tk.Label(frame_gauge, text="건식게이지").pack(side="left")
        self.entry_gauge = tk.Entry(frame_gauge)
        self.entry_gauge.pack(side="left")
        frame_gauge.pack()

        frame_structure = tk.Frame(self)
        tk.Label(frame_structure, text="구조물").pack(side="left")
        self.entry_structure = tk.Entry(frame_structure)
        self.entry_structure.pack(side="left")
        frame_structure.pack()

        frame_section = tk.Frame(self)
        tk.Label(frame_section, text="구간").pack(side="left")
        self.entry_section = tk.Entry(frame_section)
        self.entry_section.pack(side="left")
        frame_section.pack()

        frame_base_type = tk.Frame(self)
        tk.Label(frame_base_type, text="기본 타입").pack(side="left")
        self.entry_base_type = tk.Entry(frame_base_type)
        self.entry_base_type.pack(side="left")
        frame_base_type.pack()

        for e in (self.entry_post_number, self.entry_pos, self.entry_gauge,
                  self.entry_structure, self.entry_section, self.entry_base_type):
            e.pack()

        # 버튼
        tk.Button(self, text="선택 불러오기", command=self.load_selected).pack()
        tk.Button(self, text="수정 저장", command=self.save_edit).pack()
        tk.Button(self, text="전주 상세 편집", command=self.open_equipment_editor).pack()

    def on_pole_moved(self):
        self.refresh_tree()

    def on_pole_modifeyed(self):
        self.refresh_tree()

    def refresh_tree(self):
        if not self.runner.poledata:
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        for pole in self.runner.poledata:
            self.tree.insert("", "end", values=(pole.post_number, pole.pos, pole.span, pole.gauge, pole.structure, pole.section, pole.base_type , pole.radius,pole.pitch ,pole.cant, pole.z))

    def load_selected(self):
        selected = self.tree.selection()
        if selected:

            item = self.tree.item(selected[0])
            post_number, pos, span, gauge, structure, section, base_type, radius, pitch, cant ,z = item["values"]
            # epole 객체 찾기
            epole = None
            for e in self.editable_poles:
                if e.pole.pos == pos:
                    epole = e
                    break

            if self.events and epole is not None:
                self.events.emit("pole_selected", epole)

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

        for i, pole in enumerate(self.runner.poledata):
            prev_epole = self.editable_poles[i - 1] if i > 0 else None
            epole = EditablePole(pole, self.runner.structure_list,self.runner.curvelist,self.runner.pitchlist, self.runner.polyline_with_sta, prev_pole=prev_epole)
            self.editable_poles.append(epole)
            if prev_epole:
                prev_epole.next_pole = epole

    def save_edit(self):
        new_post_number = self.entry_post_number.get()
        new_pos = int(self.entry_pos.get())
        new_gauge = float(self.entry_gauge.get())
        new_section = self.entry_section.get() if not self.entry_section.get() == 'None' else None
        new_base_type = self.entry_base_type.get()
        for epole in self.editable_poles:
            if epole.pole.pos == self.original_pos:
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