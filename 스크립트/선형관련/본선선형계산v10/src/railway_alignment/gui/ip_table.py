"""
IP 파라미터 편집 테이블 (BP/EP 통합)
======================================
ttk.Treeview 기반. BP/EP는 읽기 전용(X/Y만 편집).

iid 체계:
  - "BP" : BP 행
  - "1", "2", ... : IP 행
  - "EP" : EP 행
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
    """IP 파라미터 편집 테이블 (BP/EP 포함)

    이벤트 (iid = "BP"/"EP"/"1"/"2"/...):
        on_edit(iid, field, new_value)
        on_select(iid_or_None)      — BP/EP면 None
        on_insert(iid)
        on_delete(iid)
        on_auto_toggle(ip_no, auto)
        on_type_toggle(ip_no, curve_type)
    """

    def __init__(
        self,
        master: tk.Widget,
        on_edit: Callable[[str, str, str], None],
        on_select: Optional[Callable[[Optional[int]], None]] = None,
        on_insert: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
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
    # UI
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

        # 상태 색상
        self.tree.tag_configure("error", background="#ffcdd2")
        self.tree.tag_configure("warn", background="#fff9c4")
        self.tree.tag_configure("ok", background="white")
        self.tree.tag_configure("auto_row", foreground="gray")
        self.tree.tag_configure("manual_row", foreground="black")
        self.tree.tag_configure("manual_auto_fill", foreground="black", background="#e3f2fd")
        self.tree.tag_configure("bp_ep_row", background="#f0f0f0")   # ✅ BP/EP 구분

    def _bind_events(self) -> None:
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def load_raw(self, raw_lines: list[list[str]]) -> None:
        """raw_lines로 채우기 (BP + IP + EP)"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._auto_flags.clear()
        self._type_overrides.clear()

        if not raw_lines:
            self._update_status()
            return

        # BP 행
        self._insert_bp_ep_row(raw_lines[0], "BP")

        # IP 행
        ips = raw_lines[1:-1] if len(raw_lines) >= 2 else raw_lines
        for i, row in enumerate(ips, start=1):
            try:
                y = float(row[0]); x = float(row[1])
                r = float(row[2]) if len(row) > 2 else 0.0
            except (ValueError, IndexError):
                continue

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
                    type_text, "—", "—",
                ],
                tags=("ok", "auto_row" if auto else "manual_row"),
            )

        # EP 행
        if len(raw_lines) >= 2:
            self._insert_bp_ep_row(raw_lines[-1], "EP")

        self._update_status()

    def load_curves(self, curves: list) -> None:
        """CurveParams로 IP 행 갱신 (BP/EP는 원본 유지)"""
        prev_auto = dict(self._auto_flags)
        prev_type = dict(self._type_overrides)

        # BP/EP 원본 보존
        bp_data = self.tree.item("BP", "values") if self.tree.exists("BP") else None
        ep_data = self.tree.item("EP", "values") if self.tree.exists("EP") else None

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._auto_flags.clear()
        self._type_overrides.clear()

        if bp_data:
            self.tree.insert("", "end", iid="BP", values=bp_data, tags=("ok", "bp_ep_row"))

        for curve in curves:
            self._insert_row(curve)

        if ep_data:
            self.tree.insert("", "end", iid="EP", values=ep_data, tags=("ok", "bp_ep_row"))

        # 상태 복원
        for curve in curves:
            ip_no = curve.ip_no
            self._auto_flags[ip_no] = prev_auto.get(ip_no, True)
            if ip_no in prev_type:
                self._type_overrides[ip_no] = prev_type[ip_no]
            self._apply_row_style(ip_no)
            self._set_param_cells(curve, auto=self._auto_flags[ip_no])

        self._update_status()

    def apply_validation(self, issues_by_ip: dict[int, list]) -> None:
        for iid in self.tree.get_children():
            if iid in ("BP", "EP"):
                continue
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
                type_text, l_text = "직선", "—"
            else:
                type_text, l_text = "3차포물선", f"{curve.spiral_length:.1f}"
            dir_text = "우" if curve.direction == "RIGHT CURVE" else "좌"

            self.tree.set(iid, "type", type_text)
            self.tree.set(iid, "dir", dir_text)
            self.tree.set(iid, "l", l_text)

            auto = self._auto_flags.get(curve.ip_no, True)
            self._set_param_cells(curve, auto=auto)

    def get_parameter_overrides(self) -> dict[int, dict[str, float]]:
        overrides = {}
        for iid in self.tree.get_children():
            if iid in ("BP", "EP"):
                continue
            ip_no = int(iid)
            if self._auto_flags.get(ip_no, True):
                continue
            vals = self.tree.item(iid, "values")
            try:
                m = self._parse_cell(vals[6])
                v = self._parse_cell(vals[7])
                z_m = self._parse_cell(vals[8])
            except (ValueError, IndexError):
                continue
            overrides[ip_no] = {"m": m, "v": v, "z": z_m}
        return overrides

    def get_type_overrides(self) -> dict[int, str]:
        return dict(self._type_overrides)

    def get_state(self) -> dict:
        return {
            "auto_flags": dict(self._auto_flags),
            "type_overrides": dict(self._type_overrides),
        }

    def set_state(self, state: dict) -> None:
        self._pending_auto_flags = {
            int(k): bool(v) for k, v in (state.get("auto_flags") or {}).items()
        }
        self._pending_type_overrides = {
            int(k): str(v) for k, v in (state.get("type_overrides") or {}).items()
        }

    def get_selected_iid(self) -> Optional[str]:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def get_selected_ip_no(self) -> Optional[int]:
        iid = self.get_selected_iid()
        if not iid or iid in ("BP", "EP"):
            return None
        try:
            return int(iid)
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
        s = str(text).strip().lstrip("*").strip()
        return float(s) if s else 0.0

    def _insert_bp_ep_row(self, row: list[str], iid: str) -> None:
        """BP/EP 행 삽입 (X/Y만 편집 가능)"""
        try:
            y = float(row[0]); x = float(row[1])
        except (ValueError, IndexError):
            x = y = 0.0

        self.tree.insert(
            "", "end", iid=iid,
            values=[
                "", iid, f"{x:.4f}", f"{y:.4f}",
                "—", "—", "—", "—", "—", "-", "—", "—",
            ],
            tags=("ok", "bp_ep_row"),
        )

    def _insert_row(self, curve) -> None:
        if curve.curve_type == "simplecurve":
            type_text, l_text = "단곡선", "0"
        elif curve.curve_type == "straight":
            type_text, l_text = "직선", "—"
        else:
            type_text, l_text = "3차포물선", f"{curve.spiral_length:.1f}"

        dir_text = "우" if curve.direction == "RIGHT CURVE" else "좌"
        auto = self._auto_flags.get(curve.ip_no, True)

        if auto:
            m_text = f"{curve.m:.1f}"
            v_text = f"{curve.v:.0f}"
            z_text = f"{curve.z * 0.001:.4f}"
        else:
            m_text, v_text, z_text = "0", "0", "0"

        self.tree.insert(
            "", "end", iid=str(curve.ip_no),
            values=[
                "✓" if auto else "",
                f"IP{curve.ip_no}",
                f"{curve.ip_xy[0]:.4f}",
                f"{curve.ip_xy[1]:.4f}",
                f"{curve.radius:.2f}",
                l_text,
                m_text, v_text, z_text,
                type_text, dir_text, "—",
            ],
            tags=("ok", "auto_row" if auto else "manual_row"),
        )

    def _set_param_cells(self, curve, auto: bool) -> None:
        iid = str(curve.ip_no)
        if iid in ("BP", "EP") or not self.tree.exists(iid):
            return

        if auto:
            self.tree.set(iid, "m", f"{curve.m:.1f}")
            self.tree.set(iid, "v", f"{curve.v:.0f}")
            self.tree.set(iid, "z", f"{curve.z * 0.001:.4f}")
            self._apply_row_style(curve.ip_no)
            return

        has_fill = False
        vals = self.tree.item(iid, "values")

        try:
            m_user = self._parse_cell(vals[6])
        except (ValueError, IndexError):
            m_user = 0.0
        self.tree.set(iid, "m", "0" if m_user == 0 else f"{m_user:.1f}")

        try:
            v_user = self._parse_cell(vals[7])
        except (ValueError, IndexError):
            v_user = 0.0
        if v_user == 0 and curve.curve_type == "cubic":
            self.tree.set(iid, "v", f"*{curve.v:.0f}")
            has_fill = True
        else:
            self.tree.set(iid, "v", f"{v_user:.0f}")

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

    def _apply_row_style(self, ip_no_or_iid, status_tag: Optional[str] = None,
                         has_auto_fill: bool = False) -> None:
        iid = str(ip_no_or_iid)
        if not self.tree.exists(iid) or iid in ("BP", "EP"):
            return

        try:
            ip_no = int(iid)
        except ValueError:
            return

        auto = self._auto_flags.get(ip_no, True)

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
        children = self.tree.get_children()
        ip_count = sum(1 for iid in children if iid not in ("BP", "EP"))
        auto = sum(1 for f in self._auto_flags.values() if f)
        self._status_label.config(
            text=f"IP {ip_count}개 (자동 {auto}, 수동 {ip_count - auto})"
        )

    def _on_tree_select(self, _event) -> None:
        if self._on_select is None:
            return
        iid = self.get_selected_iid()
        if iid is None:
            return
        if iid in ("BP", "EP"):
            try:
                self._on_select(None)
            except Exception:
                logger.exception("on_select 콜백 오류")
            return
        try:
            ip_no = int(iid)
            self._on_select(ip_no)
        except ValueError:
            return

    # ---------- 더블클릭 ----------
    def _on_double_click(self, event) -> None:
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col_id = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        # ✅ BP/EP: X, Y 컬럼만 편집
        if row_id in ("BP", "EP"):
            if col_id in ("#3", "#4"):   # X, Y
                self._start_edit(row_id, col_id, event)
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

        if col_key == "type":
            self._toggle_curve_type(row_id)
            return

        if col_key in _EDITABLE_KEYS:
            self._start_edit(row_id, col_id, event)
        elif col_key in _MANUAL_KEYS:
            if self._auto_flags.get(ip_no, True):
                messagebox.showinfo("안내", "자동 상태입니다. '자동' 칸을 더블클릭해 해제하세요.")
                return
            self._start_edit(row_id, col_id, event)

    def _start_edit(self, row_id: str, col_id: str, event) -> None:
        """col_id = "#3" 등 또는 컬럼 키"""
        self._cancel_edit()

        # col_id → col_key 변환
        if col_id.startswith("#"):
            try:
                col_index = int(col_id.replace("#", "")) - 1
            except ValueError:
                return
            if not (0 <= col_index < len(COLUMNS)):
                return
            col_key = COLUMNS[col_index][0]
        else:
            col_key = col_id

        col_id = f"#{self._column_index(col_key) + 1}"
        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, width, height = bbox
        value = str(self.tree.set(row_id, col_key)).lstrip("*").strip()

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
        self._on_edit(row_id, col_key, new_value)   # row_id = "BP"/"EP"/"1"...

    def _cancel_edit(self) -> None:
        if self._edit_entry is not None:
            self._edit_entry.destroy()
            self._edit_entry = None

    def _column_index(self, key: str) -> int:
        for i, (k, *_r) in enumerate(COLUMNS):
            if k == key:
                return i
        return -1

    def _toggle_auto(self, row_id: str) -> None:
        if row_id in ("BP", "EP"):
            return
        try:
            ip_no = int(row_id)
        except ValueError:
            return
        new_flag = not self._auto_flags.get(ip_no, True)
        self._auto_flags[ip_no] = new_flag
        self.tree.set(row_id, "auto", "✓" if new_flag else "")

        if not new_flag:
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
        if row_id in ("BP", "EP"):
            return
        try:
            ip_no = int(row_id)
        except ValueError:
            return
        current_text = self.tree.set(row_id, "type")
        current = self._type_overrides.get(
            ip_no, "simplecurve" if current_text == "단곡선" else "cubic",
        )
        new = "cubic" if current == "simplecurve" else "simplecurve"
        self._type_overrides[ip_no] = new
        self.tree.set(row_id, "type", "단곡선" if new == "simplecurve" else "3차포물선")

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

    def _handle_insert(self) -> None:
        iid = self.get_selected_iid() or "BP"
        if self._on_insert is not None:
            self._on_insert(iid)

    def _handle_delete(self) -> None:
        iid = self.get_selected_iid()
        if iid is None:
            messagebox.showwarning("선택 없음", "삭제할 IP를 선택하세요.")
            return
        if iid in ("BP", "EP"):
            messagebox.showwarning("삭제 불가", "BP/EP는 삭제할 수 없습니다.")
            return
        if self._on_delete is not None:
            self._on_delete(iid)