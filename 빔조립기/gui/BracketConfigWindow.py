import tkinter as tk
from tkinter import ttk, messagebox

from gui.viewmodel.bracket_input import BracketViewModel
from library import LibraryManager
from model.bracket import Bracket
from model.tkraildata import TKRailData


class BracketConfigWindow(tk.Toplevel):
    def __init__(self, master, rail: TKRailData, libmanager: LibraryManager, on_close=None, on_change=None):
        super().__init__(master)

        self.title(f"브래킷 설정 - {rail.name}")
        self.geometry("850x300")
        self.rail = rail
        self.on_close = on_close
        self.libmanager = libmanager
        self.vars = []  # 각 브래킷 행의 변수 저장
        self.on_change = on_change
        self._build_ui()
        self._load_existing()

    # =============================
    # UI
    # =============================
    def _build_ui(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        headers = ["NO","선로구분", "브래킷 종류", "X offset", "Y offset", "ROT", ""]
        for c, h in enumerate(headers):
            ttk.Label(frame, text=h, font=("맑은 고딕", 9, "bold")).grid(
                row=0, column=c, padx=5, pady=3
            )

        self.table = frame

        # 버튼 영역
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)

        ttk.Button(btns, text="＋ 브래킷 추가", command=self.add_row).pack(side="left")
        ttk.Button(btns, text="확인", command=self.apply).pack(side="right")
        ttk.Button(btns, text="취소", command=self.destroy).pack(side="right", padx=5)

    # =============================
    # 데이터 로드
    # =============================
    def _load_existing(self):
        if not self.rail.brackets:
            self.add_row()
        else:
            for b in self.rail.brackets:
                self.add_row(b)

    # =============================
    # 행 추가
    # =============================
    def add_row(self, bracket: BracketViewModel | None = None):
        row = len(self.vars) + 1

        ttk.Label(self.table, text=str(row)).grid(row=row, column=0)

        # ── 선로 타입 (행별)
        rail_type_var = tk.StringVar(value=bracket.rail_type.get() if bracket else "일반철도")

        rail_combo = ttk.Combobox(
            self.table,
            textvariable=rail_type_var,
            values=["일반철도", "도시철도", "준고속철도", "고속철도"],
            state="readonly",
            width=15
        )
        rail_combo.grid(row=row, column=1)

        # ── 브래킷 타입
        bracket_type_var = tk.StringVar(value=bracket.bracket_type.get() if bracket else "")

        def update_brackets(*_):
            self._sync_to_raildata()
            if self.on_change:
                self.on_change()  # ✅ Preview 갱신

        bracket_combo = ttk.Combobox(
            self.table,
            textvariable=bracket_type_var,
            state="readonly",
            width=30
        )
        bracket_combo.grid(row=row, column=2, padx=5)



        # ── 갱신 함수 (이 행 전용)
        def reload_brackets(*_):
            group = self.libmanager.define_group(rail_type_var.get())
            values = self.libmanager.list_files_in_category(
                category="브래킷",
                group=group
            )

            bracket_combo["values"] = values

            # ✅ 기존 값이 있으면 유지
            current = bracket_type_var.get()
            if current in values:
                bracket_combo.set(current)
            elif values:
                bracket_combo.current(0)

        rail_type_var.trace_add("write", reload_brackets)
        reload_brackets()

        # ── 기타 값
        x = tk.DoubleVar(value=bracket.xoffset.get() if bracket else 0.0)
        y = tk.DoubleVar(value=bracket.yoffset.get() if bracket else 0.0)
        r = tk.DoubleVar(value=bracket.rotation.get() if bracket else 0.0)

        for var in [rail_type_var, bracket_type_var, x, y, r]:
            var.trace_add("write", update_brackets)

        ttk.Entry(self.table, textvariable=x, width=8).grid(row=row, column=3)
        ttk.Entry(self.table, textvariable=y, width=8).grid(row=row, column=4)
        ttk.Entry(self.table, textvariable=r, width=8).grid(row=row, column=5)

        ttk.Button(
            self.table,
            text="삭제",
            command=lambda idx=row - 1: self.remove_row(idx)
        ).grid(row=row, column=6)

        self.vars.append({
            "rail_type": rail_type_var,
            "bracket_type": bracket_type_var,
            "x": x,
            "y": y,
            "r": r
        })

    # =============================
    # 행 삭제
    # =============================
    def remove_row(self, index):
        if len(self.vars) <= 1:
            messagebox.showwarning("경고", "브래킷은 최소 1개 이상 필요합니다.")
            return

        # 해당 행의 변수 제거
        self.vars.pop(index)

        # 해당 행의 위젯만 제거
        for w in self.table.grid_slaves(row=index + 1):  # 헤더가 row=0이므로 +1
            w.destroy()

        # 남은 행들의 번호 라벨 업데이트
        for i, row_vars in enumerate(self.vars, start=1):
            for w in self.table.grid_slaves(row=i):
                if isinstance(w, ttk.Label):  # 첫 번째 열 번호 라벨
                    w.config(text=str(i))

    # =============================
    # 적용
    # =============================
    def apply(self):
        self._sync_to_raildata()

        if self.on_close:
            self.on_close()

        self.destroy()

    def _sync_to_raildata(self):
        """tkRAILDATA에 저장"""
        self.rail.brackets.clear()
        for row in self.vars:
            self.rail.brackets.append(
                BracketViewModel(
                    rail_no=self.rail.index_var,
                    bracket_type=row["bracket_type"],
                    xoffset=row["x"],
                    yoffset=row["y"],
                    rotation=row["r"],
                    rail_type=row["rail_type"],
                )
            )