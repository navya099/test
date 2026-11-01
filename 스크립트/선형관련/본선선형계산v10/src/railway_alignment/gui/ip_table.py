"""
IP 파라미터 편집 테이블
========================
ttk.Treeview 기반 편집 가능 테이블. 더블클릭으로 셀 편집.

편집 가능 컬럼: X, Y, R
    - L(완화곡선 길이)은 코어 계산이 자동 산출하므로 표시 전용
    - 곡선 타입 / 방향 / 상태도 표시 전용

콜백 인자: 모두 ip_no (1-based, CurveParams.ip_no와 동일)
    raw_lines[0]=BP, raw_lines[1]=IP1, ... → raw_lines[ip_no] == 해당 IP
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from src.railway_alignment.core.validator import Severity

logger = logging.getLogger(__name__)


# 컬럼 정의: (key, title, width, anchor)
COLUMNS = [
    ("ip",     "IP",       50,  "center"),
    ("x",      "X (N)",    110, "e"),
    ("y",      "Y (E)",    110, "e"),
    ("r",      "R (m)",    90,  "e"),
    ("l",      "L (m)",    80,  "e"),
    ("type",   "곡선 타입", 110, "center"),
    ("dir",    "방향",      90,  "center"),
    ("status", "상태",      70,  "center"),
]

# 편집 가능한 컬럼 키 (L은 자동 산출이라 제외)
_EDITABLE_KEYS = {"x", "y", "r"}


class IPTableEditor(ttk.Frame):
    """IP 파라미터 편집 테이블

    이벤트 (ip_no는 1-based):
        on_edit(ip_no, field, new_value) — 셀 편집 완료 시
        on_select(ip_no)                 — 행 선택 시
        on_insert(ip_no)                 — IP 삽입 요청 (해당 IP 앞에 삽입)
        on_delete(ip_no)                 — IP 삭제 요청
    """

    def __init__(
        self,
        master: tk.Widget,
        on_edit: Callable[[int, str, str], None],
        on_select: Optional[Callable[[int], None]] = None,
        on_insert: Optional[Callable[[int], None]] = None,
        on_delete: Optional[Callable[[int], None]] = None,
    ):
        super().__init__(master)
        self._on_edit = on_edit
        self._on_select = on_select
        self._on_insert = on_insert
        self._on_delete = on_delete
        self._edit_entry: Optional[tk.Entry] = None

        self._build()
        self._bind_events()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------
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
            height=12,
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

        # 행 상태 색상
        self.tree.tag_configure("error", background="#ffcdd2")
        self.tree.tag_configure("warn", background="#fff9c4")
        self.tree.tag_configure("ok", background="white")

    def _bind_events(self) -> None:
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # --------------------------------------------------------
    # 공개 API
    # --------------------------------------------------------
    def load_curves(self, curves: list) -> None:
        """CurveParams 리스트로 테이블 채우기."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for curve in curves:
            self._insert_row(curve)

        self._update_status()

    def load_raw(self, raw_lines: list[list[str]]) -> None:
        """raw_lines로 테이블 채우기 (IP 필드만, 계산 결과 없음).

        raw_lines 포맷: [Y, X, R, ...], raw_lines[0]=BP, raw_lines[1]=IP1, ...
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 첫 줄(BP), 마지막 줄(EP) 제외 → IP1..IPN
        ips = raw_lines[1:-1] if len(raw_lines) >= 2 else raw_lines
        for i, row in enumerate(ips, start=1):
            try:
                y = float(row[0])
                x = float(row[1])
                r = float(row[2]) if len(row) > 2 else 0.0
            except (ValueError, IndexError):
                continue

            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=[
                    f"IP{i}",
                    f"{x:.4f}",
                    f"{y:.4f}",
                    f"{r:.2f}",
                    "—",
                    "(자동)",
                    "—",
                    "—",
                ],
                tags=("ok",),
            )

        self._update_status()

    def apply_validation(self, issues_by_ip: dict[int, list]) -> None:
        """검증 결과를 상태 열 + 행 색상에 반영.

        Parameters
        ----------
        issues_by_ip : dict[int, list[ValidationIssue]]
            키는 ip_no (1-based)
        """
        for iid in self.tree.get_children():
            try:
                ip_no = int(iid)
            except ValueError:
                continue

            issues = issues_by_ip.get(ip_no, [])
            if not issues:
                tag = "ok"
                status = "✓"
            else:
                has_error = any(
                    getattr(i, "severity", None) == Severity.ERROR for i in issues
                )
                tag = "error" if has_error else "warn"
                status = "✗" if has_error else "!"

            self.tree.set(iid, "status", status)
            self.tree.item(iid, tags=(tag,))

    def update_curve_columns(self, curves: list) -> None:
        """곡선 타입 / 방향 / L 열 갱신 (계산 결과 기반)."""
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

    def get_edited_curves(self) -> list[dict]:
        """테이블에서 현재 값 읽기 (편집 반영).

        반환: [{ip_no, x, y, r}, ...]
        """
        result = []
        for iid in self.tree.get_children():
            values = self.tree.item(iid, "values")
            try:
                result.append({
                    "ip_no": int(iid),
                    "x": float(values[1]),
                    "y": float(values[2]),
                    "r": float(values[3]),
                })
            except (ValueError, IndexError):
                continue
        return result

    def get_selected_ip_no(self) -> Optional[int]:
        """선택된 IP 번호 (1-based)."""
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def select_ip_no(self, ip_no: int) -> None:
        """IP 번호로 선택 (1-based)."""
        iid = str(ip_no)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)

    # --------------------------------------------------------
    # 내부
    # --------------------------------------------------------
    def _insert_row(self, curve) -> None:
        if curve.curve_type == "simplecurve":
            type_text = "단곡선"
            l_text = "0"
        else:
            type_text = "3차포물선"
            l_text = f"{curve.spiral_length:.1f}"

        dir_text = "우" if curve.direction == "RIGHT CURVE" else "좌"

        self.tree.insert(
            "",
            "end",
            iid=str(curve.ip_no),
            values=[
                f"IP{curve.ip_no}",
                f"{curve.ip_xy[0]:.4f}",
                f"{curve.ip_xy[1]:.4f}",
                f"{curve.radius:.2f}",
                l_text,
                type_text,
                dir_text,
                "—",
            ],
            tags=("ok",),
        )

    def _update_status(self) -> None:
        n = len(self.tree.get_children())
        self._status_label.config(text=f"{n}개 IP")

    def _on_tree_select(self, _event) -> None:
        if self._on_select is None:
            return
        ip_no = self.get_selected_ip_no()
        if ip_no is not None:
            self._on_select(ip_no)

    # ---------- 편집 ----------
    def _on_double_click(self, event) -> None:
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        col_id = self.tree.identify_column(event.x)
        # 컬럼 인덱스 → 키로 변환
        try:
            col_index = int(col_id.replace("#", "")) - 1
        except ValueError:
            return
        if not (0 <= col_index < len(COLUMNS)):
            return

        col_key = COLUMNS[col_index][0]
        if col_key not in _EDITABLE_KEYS:
            return

        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        self._start_edit(row_id, col_key, event)

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

        self._edit_entry.bind(
            "<Return>", lambda e: self._commit_edit(row_id, col_key)
        )
        self._edit_entry.bind("<Escape>", lambda e: self._cancel_edit())
        self._edit_entry.bind(
            "<FocusOut>", lambda e: self._commit_edit(row_id, col_key)
        )

    def _commit_edit(self, row_id: str, col_key: str) -> None:
        if self._edit_entry is None:
            return
        entry = self._edit_entry
        self._edit_entry = None      # FocusOut 재진입 방지
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

        try:
            ip_no = int(row_id)
        except ValueError:
            return

        self._on_edit(ip_no, col_key, new_value)

    def _cancel_edit(self) -> None:
        if self._edit_entry is not None:
            self._edit_entry.destroy()
            self._edit_entry = None

    def _column_index(self, key: str) -> int:
        for i, (k, *_rest) in enumerate(COLUMNS):
            if k == key:
                return i
        return -1

    # ---------- 삽입/삭제 ----------
    def _handle_insert(self) -> None:
        ip_no = self.get_selected_ip_no()
        if ip_no is None:
            ip_no = 1  # 선택 없으면 첫 IP 앞에 삽입
        if self._on_insert is not None:
            self._on_insert(ip_no)

    def _handle_delete(self) -> None:
        ip_no = self.get_selected_ip_no()
        if ip_no is None:
            messagebox.showwarning("선택 없음", "삭제할 IP를 선택하세요.")
            return
        if self._on_delete is not None:
            self._on_delete(ip_no)