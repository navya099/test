"""
IP 파라미터 편집 테이블
========================
ttk.Treeview 기반. 더블클릭 셀 편집.

컬럼:
    자동 | IP | X | Y | R | L | M | V | Z | 타입 | 방향 | 상태

자동/수동:
    - "자동" 컬럼(#1) 더블클릭 → 토글
    - 자동: M/V/Z = 계산값 표시, 회색 전경, 편집 불가
    - 수동: M/V/Z = 사용자 입력, 검정 전경, 편집 가능

단위:
    - M: 정수 (예: 2100)
    - V: 정수 (예: 270)
    - Z: m 단위 (예: 0.1600)  ← 실무 표와 동일, 서비스에 mm로 변환 전달
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from src.railway_alignment.core.validator import Severity

logger = logging.getLogger(__name__)


COLUMNS = [
    ("auto",   "자동",      45,  "center"),
    ("ip",     "IP",        50,  "center"),
    ("x",      "X (N)",     110, "e"),
    ("y",      "Y (E)",     110, "e"),
    ("r",      "R (m)",     90,  "e"),
    ("l",      "L (m)",     70,  "e"),
    ("m",      "M",         80,  "e"),
    ("v",      "V",         60,  "e"),
    ("z",      "Z (m)",     70,  "e"),
    ("type",   "곡선 타입", 100, "center"),
    ("dir",    "방향",      70,  "center"),
    ("status", "상태",      50,  "center"),
]

_EDITABLE_KEYS = {"x", "y", "r"}
_MANUAL_KEYS = {"m", "v", "z"}


class IPTableEditor(ttk.Frame):
    """IP 파라미터 편집 테이블

    이벤트 (ip_no는 1-based):
        on_edit(ip_no, field, new_value)      — 셀 편집 완료
        on_select(ip_no)                      — 행 선택
        on_insert(ip_no)                      — IP 삽입
        on_delete(ip_no)                      — IP 삭제
        on_auto_toggle(ip_no, auto: bool)     — 자동/수동 전환
    """

    def __init__(
        self,
        master: tk.Widget,
        on_edit: Callable[[int, str, str], None],
        on_select: Optional[Callable[[int], None]] = None,
        on_insert: Optional[Callable[[int], None]] = None,
        on_delete: Optional[Callable[[int], None]] = None,
        on_auto_toggle: Optional[Callable[[int, bool], None]] = None,
    ):
        super().__init__(master)
        self._on_edit = on_edit
        self._on_select = on_select
        self._on_insert = on_insert
        self._on_delete = on_delete
        self._on_auto_toggle = on_auto_toggle
        self._edit_entry: Optional[tk.Entry] = None
        self._auto_flags: dict[int, bool] = {}  # ip_no → True(자동)

        self._build()
        self._bind_events()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=4, pady=(4, 0))
        ttk.Button(toolbar, text="+ IP 삽입", command=self._handle_insert).pack(
            side="left", padx=2
        )
        ttk.Button(toolbar, text="- 삭제", command=self._handle_delete).pack(
            side="left", padx=2
        )
        self._status_label = ttk.Label(toolbar, text="", foreground="gray")
        self._status_label.pack(side="right", padx=6)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree = ttk.Treeview(
            container,
            columns=[c[0] for c in COLUMNS],
            show="headings",
            selectmode="browse",
            height=14,
        )

        for key, title, width, anchor in COLUMNS:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor=anchor, stretch=False)

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # 상태 색상 tag
        self.tree.tag_configure("error", background="#ffcdd2")
        self.tree.tag_configure("warn", background="#fff9c4")
        self.tree.tag_configure("ok", background="white")
        # 자동 상태 회색 전경
        self.tree.tag_configure("auto_row", foreground="gray")
        self.tree.tag_configure("manual_row", foreground="black")

    def _bind_events(self) -> None:
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def load_curves(self, curves: list) -> None:
        """CurveParams로 테이블 채우기 (자동 플래그 보존)."""
        prev_flags = dict(self._auto_flags)

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._auto_flags.clear()

        for curve in curves:
            self._insert_row(curve)

        # 자동 플래그 복원 (없던 IP는 자동=True)
        for curve in curves:
            self._auto_flags[curve.ip_no] = prev_flags.get(curve.ip_no, True)
            self._apply_row_style(curve.ip_no)

        # 자동 플래그가 False였던 행은 M/V/Z 재계산값 덮어쓰지 않음
        for curve in curves:
            if self._auto_flags.get(curve.ip_no, True):
                self._set_param_cells(curve)
            else:
                # 수동: 표시값 유지 (이전 load_raw 또는 편집값)
                pass

        self._update_status()

    def load_raw(self, raw_lines: list[list[str]]) -> None:
        """raw_lines로 채우기 (계산 전, 모두 자동 상태)."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._auto_flags.clear()

        ips = raw_lines[1:-1] if len(raw_lines) >= 2 else raw_lines
        for i, row in enumerate(ips, start=1):
            try:
                y = float(row[0])
                x = float(row[1])
                r = float(row[2]) if len(row) > 2 else 0.0
            except (ValueError, IndexError):
                continue

            self._auto_flags[i] = True
            self.tree.insert(
                "", "end", iid=str(i),
                values=[
                    "✓", f"IP{i}",
                    f"{x:.4f}", f"{y:.4f}", f"{r:.2f}", "—",
                    "—", "—", "—",
                    "(자동)", "—", "—",
                ],
                tags=("ok", "auto_row"),
            )
        self._update_status()

    def apply_validation(self, issues_by_ip: dict[int, list]) -> None:
        for iid in self.tree.get_children():
            try:
                ip_no = int(iid)
            except ValueError:
                continue
            issues = issues_by_ip.get(ip_no, [])
            if not issues:
                tag, status = "ok", "✓"
            else:
                has_error = any(
                    getattr(i, "severity", None) == Severity.ERROR for i in issues
                )
                tag = "error" if has_error else "warn"
                status = "✗" if has_error else "!"

            self.tree.set(iid, "status", status)
            base_tags = (tag, "auto_row" if self._auto_flags.get(ip_no, True) else "manual_row")
            self.tree.item(iid, tags=base_tags)

    def update_curve_columns(self, curves: list) -> None:
        """계산 결과로 L/타입/방향/M/V/Z 갱신."""
        for curve in curves:
            iid = str(curve.ip_no)
            if not self.tree.exists(iid):
                continue

            if curve.curve_type == "simplecurve":
                type_text = "단곡선"
                l_text = "0"
            else:
                type_text = "3차포물선"
                l_text = f"{curve.spiral_length:.1f}"
            dir_text = "우" if curve.direction == "RIGHT CURVE" else "좌"

            self.tree.set(iid, "type", type_text)
            self.tree.set(iid, "dir", dir_text)
            self.tree.set(iid, "l", l_text)

            # 자동 상태일 때만 계산값 반영
            if self._auto_flags.get(curve.ip_no, True):
                self._set_param_cells(curve)

    def get_parameter_overrides(self) -> dict[int, dict[str, float]]:
        """자동 해제된 IP의 M/V/Z를 서비스용 dict로 반환.

        - m: 그대로 (정수 단위 반올림은 서비스에서)
        - v: 정수 (서비스에서 10단위 반올림)
        - z: **mm 단위**로 변환 (테이블 m → ×1000)
        """
        overrides: dict[int, dict[str, float]] = {}
        for iid in self.tree.get_children():
            ip_no = int(iid)
            if self._auto_flags.get(ip_no, True):
                continue
            vals = self.tree.item(iid, "values")
            try:
                m = float(vals[6])
                v = float(vals[7])
                z_m = float(vals[8])           # 표시: m 단위
            except (ValueError, IndexError):
                continue
            overrides[ip_no] = {"m": m, "v": v, "z": z_m * 1000.0}
        return overrides

    def get_selected_ip_no(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def select_ip_no(self, ip_no: int) -> None:
        iid = str(ip_no)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------
    def _insert_row(self, curve) -> None:
        if curve.curve_type == "simplecurve":
            type_text, l_text = "단곡선", "0"
        else:
            type_text, l_text = "3차포물선", f"{curve.spiral_length:.1f}"
        dir_text = "우" if curve.direction == "RIGHT CURVE" else "좌"

        # 기본값: 자동 상태로 초기 생성
        auto = self._auto_flags.get(curve.ip_no, True)

        self.tree.insert(
            "", "end", iid=str(curve.ip_no),
            values=[
                "✓" if auto else "",
                f"IP{curve.ip_no}",
                f"{curve.ip_xy[0]:.4f}",
                f"{curve.ip_xy[1]:.4f}",
                f"{curve.radius:.2f}",
                l_text,
                f"{curve.m:.1f}" if auto else "",   # M
                f"{curve.v:.0f}" if auto else "",   # V
                f"{curve.z * 0.001:.4f}" if auto else "",   # Z(mm → m 표시)
                type_text, dir_text, "—",
            ],
            tags=("ok", "auto_row" if auto else "manual_row"),
        )

    def _set_param_cells(self, curve) -> None:
        """자동 모드에서 M/V/Z 셀 갱신."""
        iid = str(curve.ip_no)
        self.tree.set(iid, "m", f"{curve.m:.1f}")
        self.tree.set(iid, "v", f"{curve.v:.0f}")
        self.tree.set(iid, "z", f"{curve.z * 0.001:.4f}")   # mm → m

    def _apply_row_style(self, ip_no: int) -> None:
        iid = str(ip_no)
        if not self.tree.exists(iid):
            return
        auto = self._auto_flags.get(ip_no, True)
        current = self.tree.item(iid, "tags") or ()
        # 기존 상태 tag 유지 (error/warn/ok)
        status_tags = tuple(t for t in current if t in ("error", "warn", "ok"))
        if not status_tags:
            status_tags = ("ok",)
        self.tree.item(
            iid,
            tags=status_tags + ("auto_row" if auto else "manual_row",),
        )

    def _update_status(self) -> None:
        n = len(self.tree.get_children())
        auto = sum(1 for f in self._auto_flags.values() if f)
        self._status_label.config(text=f"{n}개 IP (자동 {auto}, 수동 {n - auto})")

    def _on_tree_select(self, _event) -> None:
        if self._on_select is None:
            return
        ip_no = self.get_selected_ip_no()
        if ip_no is not None:
            self._on_select(ip_no)

    # ---------- 더블클릭 ----------
    def _on_double_click(self, event) -> None:
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col_id = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        # 자동 토글 (#1)
        if col_id == "#1":
            self._toggle_auto(row_id)
            return

        try:
            col_index = int(col_id.replace("#", "")) - 1
        except ValueError:
            return
        if not (0 <= col_index < len(COLUMNS)):
            return
        col_key = COLUMNS[col_index][0]

        ip_no = int(row_id)
        auto = self._auto_flags.get(ip_no, True)

        if col_key in _EDITABLE_KEYS:
            self._start_edit(row_id, col_key, event)
        elif col_key in _MANUAL_KEYS:
            if auto:
                messagebox.showinfo("안내", "자동 상태입니다. '자동' 칸을 더블클릭해 해제하세요.")
                return
            self._start_edit(row_id, col_key, event)

    def _toggle_auto(self, row_id: str) -> None:
        ip_no = int(row_id)
        new_flag = not self._auto_flags.get(ip_no, True)
        self._auto_flags[ip_no] = new_flag
        self.tree.set(row_id, "auto", "✓" if new_flag else "")
        self._apply_row_style(ip_no)

        if not new_flag:
            # 수동으로 전환: 현재 표시된 값 유지 (이미 계산값이 있으면 그걸 시작점으로)
            pass  # 이후 재계산 시 get_parameter_overrides가 무시 → 서비스는 auto값 사용

        if self._on_auto_toggle is not None:
            try:
                self._on_auto_toggle(ip_no, new_flag)
            except Exception:
                logger.exception("on_auto_toggle 콜백 오류")

    def _start_edit(self, row_id: str, col_key: str, event) -> None:
        self._cancel_edit()
        col_id = f"#{self._column_index(col_key) + 1}"
        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, width, height = bbox
        value = self.tree.set(row_id, col_key)

        self._edit_entry = tk.Entry(self.tree)
        self._edit_entry.insert(0, value)
        self._edit_entry.select_range(0, "end")
        self._edit_entry.place(x=x, y=y, width=width, height=height)
        self._edit_entry.focus_set()

        self._edit_entry.bind("<Return>", lambda e: self._commit_edit(row_id, col_key))
        self._edit_entry.bind("<Escape>", lambda e: self._cancel_edit())
        self._edit_entry.bind("<FocusOut>", lambda e: self._commit_edit(row_id, col_key))

    def _commit_edit(self, row_id: str, col_key: str) -> None:
        if self._edit_entry is None:
            return
        entry = self._edit_entry
        self._edit_entry = None
        new_value = entry.get().strip()
        entry.destroy()

        if not new_value:
            return
        try:
            float(new_value)
        except ValueError:
            messagebox.showerror("입력 오류", f"숫자를 입력하세요: {new_value}")
            return

        self.tree.set(row_id, col_key, new_value)
        ip_no = int(row_id)
        self._on_edit(ip_no, col_key, new_value)

    def _cancel_edit(self) -> None:
        if self._edit_entry is not None:
            self._edit_entry.destroy()
            self._edit_entry = None

    def _column_index(self, key: str) -> int:
        for i, (k, *_r) in enumerate(COLUMNS):
            if k == key:
                return i
        return -1

    def _handle_insert(self) -> None:
        ip_no = self.get_selected_ip_no() or 1
        if self._on_insert is not None:
            self._on_insert(ip_no)

    def _handle_delete(self) -> None:
        ip_no = self.get_selected_ip_no()
        if ip_no is None:
            messagebox.showwarning("선택 없음", "삭제할 IP를 선택하세요.")
            return
        if self._on_delete is not None:
            self._on_delete(ip_no)