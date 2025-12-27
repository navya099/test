import tkinter as tk
from tkinter import ttk, messagebox

from library import LibraryManager
from model.bracket import Bracket
from model.raildata import RailData


class BracketConfigWindow(tk.Toplevel):
    def __init__(self, master, rail: RailData,libmanager: LibraryManager, on_close=None):
        super().__init__(master)

        self.title(f"브래킷 설정 - {rail.name}")
        self.geometry("850x300")
        self.rail = rail
        self.on_close = on_close
        self.libmanager = libmanager
        self.vars = []  # 각 브래킷 행의 변수 저장

        self._build_ui()
        self._load_existing()

        self.grab_set()  # 모달 처리

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
    def add_row(self, bracket: Bracket | None = None):
        row = len(self.vars) + 1

        ttk.Label(self.table, text=str(row)).grid(row=row, column=0)

        # ── 선로 타입 (행별)
        rail_type_var = tk.StringVar(value=bracket.rail_type if bracket else "일반철도")

        rail_combo = ttk.Combobox(
            self.table,
            textvariable=rail_type_var,
            values=["일반철도", "도시철도", "준고속철도", "고속철도"],
            state="readonly",
            width=15
        )
        rail_combo.grid(row=row, column=1)

        # ── 브래킷 타입
        bracket_type_var = tk.StringVar(value=bracket.type if bracket else "")

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
            if values:
                bracket_combo.current(0)

        rail_type_var.trace_add("write", reload_brackets)
        reload_brackets()

        # ── 기타 값
        x = tk.DoubleVar(value=bracket.xoffset if bracket else 0.0)
        y = tk.DoubleVar(value=bracket.yoffset if bracket else 0.0)
        r = tk.DoubleVar(value=bracket.rotation if bracket else 0.0)

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

        self.vars.pop(index)

        for w in self.table.winfo_children():
            w.destroy()

        self.vars_copy = self.vars[:]
        self.vars.clear()

        for v in self.vars_copy:
            self.add_row(
                Bracket(
                    rail_no=self.rail.index,
                    type=v[0].get(),
                    xoffset=v[1].get(),
                    yoffset=v[2].get(),
                    rotation=v[3].get(),
                    index=0
                )
            )

    # =============================
    # 적용
    # =============================
    def apply(self):
        self.rail.brackets.clear()

        for row in self.vars:
            self.rail.brackets.append(
                Bracket(
                    rail_no=self.rail.index,
                    type=row["bracket_type"].get(),
                    xoffset=row["x"].get(),
                    yoffset=row["y"].get(),
                    rotation=row["r"].get(),
                    index=0
                )
            )

        if self.on_close:
            self.on_close()

        self.destroy()
