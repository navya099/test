"""
IP 파라미터 편집 테이블
========================
ttk.Treeview 기반. 더블클릭 셀 편집.

자동/수동:
    - "자동" 컬럼(#1) 더블클릭 → 토글
    - 자동: M/V/Z = 계산값, 회색, 편집 불가
    - 수동: M/V/Z = 사용자 입력(초기 0), 검정, 편집 가능

자동 재계산 표식:
    - 수동 상태에서 V/Z=0이면 서비스가 자동값으로 대체
    - 테이블은 실제 사용된 자동값 앞에 '*' 표식 + 파란색 배경(연한 파랑)

곡선 타입:
    - 'type' 컬럼 더블클릭 → "원곡선" ↔ "3차포물선" 토글
    - 토글 시 자동 플래그 자동 해제

Z 단위:
    - 표시: m 단위 (예: 0.1600)
    - 서비스 전달: m 그대로 (서비스가 mm로 변환)
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
    ("v",      "V",         70,  "e"),
    ("z",      "Z (m)",     70,  "e"),
    ("type",   "곡선 타입", 100, "center"),
    ("dir",    "방향",      70,  "center"),
    ("status", "상태",      50,  "center"),
]

_EDITABLE_KEYS = {"x", "y", "r"}
_MANUAL_KEYS = {"m", "v", "z"}


class IPTableEditor(ttk.Frame):
    """IP 파라미터 편집 테이블"""

    def __init__(
        self,
        master: tk.Widget,
        on_edit: Callable[[int, str, str], None],
        on_select: Optional[Callable[[int], None]] = None,
        on_insert: Optional[Callable[[int], None]] = None,
        on_delete: Optional[Callable[[int], None]] = None,
        on_auto_toggle: Optional[Callable[[int, bool], None]] = None,
        on_type_toggle: Optional[Callable[[int, str], None]] = None,
    ):
        super().__init__(master)
        self._on_edit = on_edit
        self._on_select = on_select
        self._on_insert = on_insert
        self._on_delete = on_delete
        self._on_auto_toggle = on_auto_toggle
        self._on_type_toggle = on_type_toggle

        self._edit_entry: Optional[tk.Entry] = None
        self._auto_flags: dict[int, bool] = {}
        self._type_overrides: dict[int, str] = {}
        self._pending_auto_flags: dict[int, bool] = {}
        self._pending_type_overrides: dict[int, str] = {}

        self._build()
        self._bind_events()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=4, pady=(4, 0))
        ttk.Button(toolbar, text="+ IP 삽입", command=self._handle_insert).pack(side="left", padx=2)
        ttk.Button(toolbar, text="- 삭제", command=self._handle_delete).pack(side="left", padx=2)
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

        # 상태 + 자동/수동 + 자동재계산 배경
        self.tree.tag_configure("error", background="#ffcdd2")
        self.tree.tag_configure("warn", background="#fff9c4")
        self.tree.tag_configure("ok", background="white")

        self.tree.tag_configure("auto_row", foreground="gray", background="white")
        self.tree.tag_configure("manual_row", foreground="black", background="white")
        # 수동인데 V/Z가 자동 재계산된 값을 포함한 행
        self.tree.tag_configure("manual_auto_fill", foreground="black", background="#e3f2fd")

    def _bind_events(self) -> None:
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def load_curves(self, curves: list) -> None:
        prev_auto = dict(self._auto_flags)
        prev_type = dict(self._type_overrides)

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._auto_flags.clear()
        self._type_overrides.clear()

        for curve in curves:
            self._insert_row(curve)

        for curve in curves:
            ip_no = curve.ip_no
            self._auto_flags[ip_no] = prev_auto.get(ip_no, True)
            if ip_no in prev_type:
                self._type_overrides[ip_no] = prev_type[ip_no]
            self._apply_row_style(ip_no)
            self._set_param_cells(curve, auto=self._auto_flags[ip_no])

        self._update_status()

    def load_raw(self, raw_lines):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._auto_flags.clear()
        self._type_overrides.clear()

        ips = raw_lines[1:-1] if len(raw_lines) >= 2 else raw_lines
        for i, row in enumerate(ips, start=1):
            try:
                y = float(row[0]);
                x = float(row[1])
                r = float(row[2]) if len(row) > 2 else 0.0
            except (ValueError, IndexError):
                continue

            # ✅ pending 상태 우선
            auto = self._pending_auto_flags.get(i, True)
            self._auto_flags[i] = auto
            if i in self._pending_type_overrides:
                self._type_overrides[i] = self._pending_type_overrides[i]

            type_text = "(자동)" if auto else (
                "직선" if r == 0 else "3차포물선"
            )
            self.tree.insert(
                "", "end", iid=str(i),
                values=[
                    "✓" if auto else "",
                    f"IP{i}",
                    f"{x:.4f}", f"{y:.4f}", f"{r:.2f}", "—",
                    "—" if auto else "0",
                    "—" if auto else "0",
                    "—" if auto else "0",
                    type_text,
                    "—",
                    "—",
                ],
                tags=("ok", "auto_row" if auto else "manual_row"),
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
                has_error = any(getattr(i, "severity", None) == Severity.ERROR for i in issues)
                tag = "error" if has_error else "warn"
                status = "✗" if has_error else "!"
            self.tree.set(iid, "status", status)
            self._apply_row_style(ip_no, status_tag=tag)

    def update_curve_columns(self, curves: list) -> None:
        for curve in curves:
            iid = str(curve.ip_no)
            if not self.tree.exists(iid):
                continue

            if curve.curve_type == "simplecurve":
                type_text, l_text = "단곡선", "0"
            elif curve.curve_type == "straight":
                type_text, l_text = "직선", "—"  # ✅
            else:
                type_text, l_text = "3차포물선", f"{curve.spiral_length:.1f}"

            dir_text = "우" if curve.direction == "RIGHT CURVE" else "좌"
            self.tree.set(iid, "type", type_text)
            self.tree.set(iid, "dir", dir_text)
            self.tree.set(iid, "l", l_text)

            auto = self._auto_flags.get(curve.ip_no, True)
            self._set_param_cells(curve, auto=auto)

    def get_parameter_overrides(self) -> dict[int, dict[str, float]]:
        """자동 해제된 IP의 M/V/Z (z는 m 단위 그대로)."""
        overrides: dict[int, dict[str, float]] = {}
        for iid in self.tree.get_children():
            ip_no = int(iid)
            if self._auto_flags.get(ip_no, True):
                continue
            # ✅ R=0 (직선 IP) 무시
            r_text = self.tree.set(iid, "r")
            try:
                if float(r_text) == 0:
                    continue
            except (ValueError, TypeError):
                continue

            vals = self.tree.item(iid, "values")
            try:
                # '*' 표식 제거
                m = self._parse_cell(vals[6])
                v = self._parse_cell(vals[7])
                z_m = self._parse_cell(vals[8])
            except (ValueError, IndexError):
                continue
            overrides[ip_no] = {"m": m, "v": v, "z": z_m}
        return overrides

    def get_type_overrides(self) -> dict[int, str]:
        """사용자가 명시 토글한 타입만 반환 (M/V/Z 규칙은 서비스 처리)."""
        return dict(self._type_overrides)

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
    @staticmethod
    def _parse_cell(text: str) -> float:
        """셀 값 파싱 ('*' 표식 제거)."""
        s = str(text).strip().lstrip("*").strip()
        return float(s) if s else 0.0

    def _insert_row(self, curve) -> None:
        if curve.curve_type == "simplecurve":
            type_text, l_text = "단곡선", "0"
        elif curve.curve_type == "straight":
            type_text, l_text = "직선", "—"  # ✅
        else:
            type_text, l_text = "3차포물선", f"{curve.spiral_length:.1f}"
        dir_text = "우" if curve.direction == "RIGHT CURVE" else "좌"  # ✅
        auto = self._auto_flags.get(curve.ip_no, True)

        if auto:
            m_text = f"{curve.m:.1f}"
            v_text = f"{curve.v:.0f}"
            z_text = f"{curve.z * 0.001:.4f}"
        else:
            m_text, v_text, z_text = "0", "0", "0"

        self.tree.insert(
            "", "end", iid=str(curve.ip_no),
            values=["✓" if auto else "", f"IP{curve.ip_no}",
                    f"{curve.ip_xy[0]:.4f}", f"{curve.ip_xy[1]:.4f}",
                    f"{curve.radius:.2f}", l_text,
                    m_text, v_text, z_text,
                    type_text, dir_text, "—"],
            tags=("ok", "auto_row" if auto else "manual_row"),
        )

    def _set_param_cells(self, curve, auto: bool) -> None:
        """M/V/Z 셀 갱신.
        - 자동: 실제 계산값
        - 수동: 사용자 입력값 유지. 단, 0이면 자동 재계산된 값에 '*' 표식
        """
        iid = str(curve.ip_no)
        if auto:
            self.tree.set(iid, "m", f"{curve.m:.1f}")
            self.tree.set(iid, "v", f"{curve.v:.0f}")
            self.tree.set(iid, "z", f"{curve.z * 0.001:.4f}")
            self._apply_row_style(curve.ip_no)
            return

        # 수동: 현재 셀 값 유지 + 0인 항목만 '*' 표식
        has_fill = False
        vals = self.tree.item(iid, "values")

        # M: 0이면 원곡선 확정이므로 M 셀은 사용자 그대로
        try:
            m_user = self._parse_cell(vals[6])
        except (ValueError, IndexError):
            m_user = 0.0
        if m_user != 0:
            self.tree.set(iid, "m", f"{m_user:.1f}")
        else:
            self.tree.set(iid, "m", "0")

        # V: 0이면 자동값 + '*'
        try:
            v_user = self._parse_cell(vals[7])
        except (ValueError, IndexError):
            v_user = 0.0
        if v_user == 0 and curve.curve_type == "cubic":
            self.tree.set(iid, "v", f"*{curve.v:.0f}")
            has_fill = True
        else:
            self.tree.set(iid, "v", f"{v_user:.0f}")

        # Z: 0이면 자동값 + '*'
        try:
            z_user = self._parse_cell(vals[8])
        except (ValueError, IndexError):
            z_user = 0.0
        if z_user == 0 and curve.curve_type == "cubic":
            self.tree.set(iid, "z", f"*{curve.z * 0.001:.4f}")
            has_fill = True
        else:
            self.tree.set(iid, "z", f"{z_user:.4f}")

        self._apply_row_style(curve.ip_no, has_auto_fill=has_fill)

    def _apply_row_style(self, ip_no: int, status_tag: Optional[str] = None,
                         has_auto_fill: bool = False) -> None:
        iid = str(ip_no)
        if not self.tree.exists(iid):
            return
        auto = self._auto_flags.get(ip_no, True)

        # 기존 status tag 유지
        if status_tag is None:
            current = self.tree.item(iid, "tags") or ()
            for t in ("error", "warn", "ok"):
                if t in current:
                    status_tag = t
                    break
            else:
                status_tag = "ok"

        if auto:
            mode_tag = "auto_row"
        elif has_auto_fill:
            mode_tag = "manual_auto_fill"
        else:
            mode_tag = "manual_row"

        self.tree.item(iid, tags=(status_tag, mode_tag))

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

        if col_key == "type":
            self._toggle_curve_type(row_id)
            return

        if col_key in _EDITABLE_KEYS:
            self._start_edit(row_id, col_key, event)
        elif col_key in _MANUAL_KEYS:
            if self._auto_flags.get(ip_no, True):
                messagebox.showinfo("안내", "자동 상태입니다. '자동' 칸을 더블클릭해 해제하세요.")
                return
            self._start_edit(row_id, col_key, event)

    def _toggle_auto(self, row_id: str) -> None:
        ip_no = int(row_id)
        new_flag = not self._auto_flags.get(ip_no, True)
        self._auto_flags[ip_no] = new_flag
        self.tree.set(row_id, "auto", "✓" if new_flag else "")

        if not new_flag:
            # 수동 전환: M/V/Z 0으로 초기화
            self.tree.set(row_id, "m", "0")
            self.tree.set(row_id, "v", "0")
            self.tree.set(row_id, "z", "0")

        self._apply_row_style(ip_no)

        if self._on_auto_toggle is not None:
            try:
                self._on_auto_toggle(ip_no, new_flag)
            except Exception:
                logger.exception("on_auto_toggle 콜백 오류")

    def _toggle_curve_type(self, row_id: str) -> None:
        ip_no = int(row_id)
        current_text = self.tree.set(row_id, "type")
        current = self._type_overrides.get(
            ip_no, "simplecurve" if current_text == "단곡선" else "cubic",
        )
        new = "cubic" if current == "simplecurve" else "simplecurve"
        self._type_overrides[ip_no] = new
        self.tree.set(row_id, "type", "단곡선" if new == "simplecurve" else "3차포물선")

        # 타입 토글 시 자동 해제
        if self._auto_flags.get(ip_no, True):
            self._auto_flags[ip_no] = False
            self.tree.set(row_id, "auto", "")
            self.tree.set(row_id, "m", "0")
            self.tree.set(row_id, "v", "0")
            self.tree.set(row_id, "z", "0")
            self._apply_row_style(ip_no)

        if self._on_type_toggle is not None:
            try:
                self._on_type_toggle(ip_no, new)
            except Exception:
                logger.exception("on_type_toggle 콜백 오류")

    def _start_edit(self, row_id: str, col_key: str, event) -> None:
        self._cancel_edit()
        col_id = f"#{self._column_index(col_key) + 1}"
        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, width, height = bbox
        value = self.tree.set(row_id, col_key)
        # '*' 표식 제거하고 편집 시작
        value = str(value).lstrip("*").strip()

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

    def get_state(self) -> dict:
        """현재 테이블 상태 (저장용)"""
        return {
            "auto_flags": dict(self._auto_flags),
            "type_overrides": dict(self._type_overrides),
        }

    def set_state(self, state: dict) -> None:
        """상태 복원 (재계산 전 호출).

        load_raw/load_curves가 내부 상태를 리셋하므로,
        복원은 load_raw 직전에 호출 후 load_raw가 보존하도록 처리.
        """
        self._pending_auto_flags = {
            int(k): bool(v) for k, v in (state.get("auto_flags") or {}).items()
        }
        self._pending_type_overrides = {
            int(k): str(v) for k, v in (state.get("type_overrides") or {}).items()
        }