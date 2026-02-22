import tkinter as tk

from gui.viewmodel.bracket_fitting_vm import BracketFittingViewModel
from gui.viewmodel.bracket_input import BracketViewModel
from library import LibraryManager
from tkinter import ttk, messagebox

class BracketFittingConfigWindow(tk.Toplevel):
    def __init__(self, master, bracket: BracketViewModel, libmanager: LibraryManager, on_close=None, on_change=None):
        super().__init__(master)
        self.bracket = bracket
        self._bracket_cache = {}  # ✅ 반드시 먼저
        self._isloading = False  # ✅ 이것도 같이
        self.title("브래킷 금구류 설정")
        self.geometry("850x300")
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

        headers = ["NO","선로구분", "금구류 종류", "X offset", "Y offset", "ROT", ""]
        for c, h in enumerate(headers):
            ttk.Label(frame, text=h, font=("맑은 고딕", 9, "bold")).grid(
                row=0, column=c, padx=5, pady=3
            )

        self.table = frame

        # 버튼 영역
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)

        ttk.Button(btns, text="＋ 금구류 추가", command=self.add_row).pack(side="left")
        ttk.Button(btns, text="확인", command=self.apply).pack(side="right")
        ttk.Button(btns, text="취소", command=self.destroy).pack(side="right", padx=5)

    # =============================
    # 데이터 로드
    # =============================
    def _load_existing(self):
        self.master.isloading = True
        if self.bracket:
            if not self.bracket.fittings:
                self.add_row()
            else:
                for f in self.bracket.fittings:
                    self.add_row(f)
        else:
            messagebox.showinfo('정보','선택된 브래킷이 없습니다. 먼저 브래킷을 선택해주세요')
            return
        self.master.isloading = False

        if self.on_change:
            self.on_change()
            # =============================
    # 행 추가
    # =============================
    def add_row(self, fitting: BracketFittingViewModel | None = None):
        row = len(self.vars) + 1

        ttk.Label(self.table, text=str(row)).grid(row=row, column=0)

        # ── 선로 타입 (행별)
        rail_type_var = tk.StringVar(value=self.bracket.rail_type.get() if self.bracket else "일반철도")

        rail_combo = ttk.Combobox(
            self.table,
            textvariable=rail_type_var,
            values=["일반철도", "도시철도", "준고속철도", "고속철도"],
            state="readonly",
            width=15
        )
        rail_combo.grid(row=row, column=1)

        # ── 금구류 이름
        fitting_type_var = tk.StringVar(value=fitting.name_var.get() if fitting else "")


        def update_brackets(*_):
            if self.master.isloading:
                return

            self._sync_to_raildata()

            if self.on_change:
                if self._preview_after:
                    self.after_cancel(self._preview_after)

                self._preview_after = self.after(200, self.on_change)

        fitting_combo = ttk.Combobox(
            self.table,
            textvariable=fitting_type_var,
            state="readonly",
            width=30
        )
        fitting_combo.grid(row=row, column=2, padx=5)

        # ── 갱신 함수 (이 행 전용)
        def reload_brackets(*_):
            rail_type = rail_type_var.get()
            group = self.libmanager.define_group(rail_type)

            if group not in self._bracket_cache:
                self._bracket_cache[group] = self.libmanager.list_files_in_category(
                    category="브래킷",
                    group=group
                )

            values = self._bracket_cache[group]
            fitting_combo["values"] = values

            current = fitting_type_var.get()
            if current in values:
                fitting_combo.set(current)
            elif values:
                fitting_combo.current(0)

        rail_type_var.trace_add("write", reload_brackets)
        reload_brackets()

        # ── 기타 값
        x = tk.DoubleVar(value=fitting.xoffset.get() if fitting else 0.0)
        y = tk.DoubleVar(value=fitting.yoffset.get() if fitting else 0.0)
        r = tk.DoubleVar(value=fitting.rotation.get() if fitting else 0.0)

        for var in [rail_type_var, fitting_type_var, x, y, r]:
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
            "fitting_type": fitting_type_var,
            "x": x,
            "y": y,
            "r": r
        })
    # =============================
    # 행 삭제
    # =============================
    def remove_row(self, index):
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
        """tkBracketmodel에 저장"""
        self.bracket.fittings.clear()
        for row in self.vars:
            self.bracket.fittings.append(
                BracketFittingViewModel(
                    name_var=row["fitting_type"],
                    xoffset=row["x"],
                    yoffset=row["y"],
                    rotation=row["r"],
                )
            )