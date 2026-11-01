"""
도면 설정 다이얼로그
=====================
레이어/색상/선종류 + 크기/오프셋 편집. JSON 프리셋 지원.
"""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from src.railway_alignment.io.dxf_config import (
    ACI_BY_VALUE,
    ACI_COLORS,
    DXFConfig,
    LayerStyle, SCALE_PRESETS, ScalePreset, apply_preset_to_config, IMPLEMENTED_BLOCK_TYPES, IP_BLOCK_TYPES,
)

logger = logging.getLogger(__name__)

# 라벨 ↔ id 매핑 (모듈 레벨)
_TYPE_LABEL_MAP: dict[str, str] = {
    tid: (label if tid in IMPLEMENTED_BLOCK_TYPES else f"{label} (미구현)")
    for tid, label in IP_BLOCK_TYPES
}

_TYPE_ID_BY_LABEL: dict[str, str] = {v: k for k, v in _TYPE_LABEL_MAP.items()}

# 레이어 필드 (표시 이름)
_LAYER_FIELDS: list[tuple[str, str]] = [
    ("layer_fl",           "선형(FL)"),
    ("layer_ip_line",      "IP 연결선"),
    ("layer_ip_intersect", "IP 교점선"),
    ("layer_ip_text",      "IP 문자"),
    ("layer_ip_table",     "IP 제원표"),
    ("layer_km_symbol",    "km 심볼"),
    ("layer_sub_symbol",   "m 심볼"),
    ("layer_km_text",      "km 문자"),
    ("layer_sub_text",     "m 문자"),
    ("layer_aux_station",  "보조 측점"),
    ("layer_curve_leader", "곡선 인출선"),
    ("layer_curve_text",   "곡선 제원 문자"),
]

_SIZE_FIELDS = [
    ("text_height",         "문자 높이 (m)"),
    ("const_width",          "선 굵기 (m)"),              # ✅ 신규
    ("km_symbol_radius",    "주 심볼 반경 (m)"),
    ("sub_symbol_radius",   "보조 심볼 반경 (m)"),
    ("tick_half_length",    "틱 반장 (m)"),
    ("leader_length",       "곡선 인출선 길이 (m)"),
    ("ip_intersect_short",  "IP 교점선 짧은 (m)"),
    ("ip_intersect_long",   "IP 교점선 긴 (m)"),
    ("ip_block_line_spacing","IP 제원표 행 간격 (m)"),
    ("curve_text_offset_far", "곡선 문자 오프셋 <10km (m)"),
    ("curve_text_offset_mid", "곡선 문자 오프셋 10~100km (m)"),
    ("curve_text_offset_near","곡선 문자 오프셋 100km+ (m)"),
]

class DXFSettingsDialog(tk.Toplevel):
    """도면 설정 모달 다이얼로그.

    on_apply(config) : 적용 버튼 → 부모에 전달
    """

    def __init__(
        self,
        master: tk.Widget,
        config: DXFConfig,
        on_apply: Optional[Callable[[DXFConfig], None]] = None,
    ):
        super().__init__(master)
        self.title("도면 설정")
        self.geometry("760x640")
        self.transient(master)
        self.grab_set()

        # 복사본 사용 (취소 시 원본 유지)
        self._config = DXFConfig.from_dict(config.to_dict())
        self._on_apply = on_apply

        # 위젯 참조
        self._layer_rows: dict[str, str] = {}       # key → tree iid
        self._size_vars: dict[str, tk.StringVar] = {}

        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self._tab_layers = ttk.Frame(nb)
        nb.add(self._tab_layers, text="레이어 & 색상")
        self._build_layers_tab()

        self._tab_sizes = ttk.Frame(nb)
        nb.add(self._tab_sizes, text="크기 & 오프셋")
        self._build_sizes_tab()

        self._tab_preset = ttk.Frame(nb)
        nb.add(self._tab_preset, text="프리셋")
        self._build_preset_tab()

        # 하단 버튼
        btn = ttk.Frame(self)
        btn.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btn, text="적용", command=self._on_apply_clicked).pack(side="right", padx=4)
        ttk.Button(btn, text="취소", command=self.destroy).pack(side="right", padx=4)

    # ---------------- 탭1: 레이어 ----------------
    def _build_layers_tab(self) -> None:
        frame = self._tab_layers
        cols = ("label", "name", "color", "linetype")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=13)
        tree.heading("label", text="항목")
        tree.heading("name", text="레이어명")
        tree.heading("color", text="색상")
        tree.heading("linetype", text="선종류")
        tree.column("label",    width=160, anchor="w")
        tree.column("name",     width=220, anchor="w")
        tree.column("color",    width=120, anchor="center")
        tree.column("linetype", width=140, anchor="center")
        tree.pack(fill="both", expand=True, padx=4, pady=4)
        self._layer_tree = tree

        for key, label in _LAYER_FIELDS:
            lyr: LayerStyle = getattr(self._config, key)
            iid = tree.insert(
                "", "end",
                values=(label, lyr.name, ACI_BY_VALUE.get(lyr.color, str(lyr.color)), lyr.linetype),
            )
            self._layer_rows[key] = iid

        tree.bind("<Double-1>", self._on_layer_double_click)

        hint = ttk.Label(
            frame,
            text="더블클릭: 레이어명/선종류 편집, 색상 셀 클릭 시 색상 선택",
            foreground="gray",
        )
        hint.pack(fill="x", padx=4, pady=(0, 4))

    def _on_layer_double_click(self, event) -> None:
        tree = self._layer_tree
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = tree.identify_column(event.x)
        row = tree.identify_row(event.y)
        if not row:
            return

        key = next((k for k, iid in self._layer_rows.items() if iid == row), None)
        if key is None:
            return
        style: LayerStyle = getattr(self._config, key)

        if col == "#2":
            self._edit_cell(row, col, style.name,
                            lambda v: self._set_layer_name(key, row, v))
        elif col == "#3":
            self._pick_color(key, row)
        elif col == "#4":
            self._edit_cell(row, col, style.linetype,
                            lambda v: self._set_linetype(key, row, v))

    def _edit_cell(self, row: str, col: str, initial: str, on_commit) -> None:
        bbox = self._layer_tree.bbox(row, col)
        if not bbox:
            return
        x, y, w, h = bbox
        entry = ttk.Entry(self._layer_tree)
        entry.insert(0, initial)
        entry.select_range(0, "end")
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()

        def commit(_e=None):
            on_commit(entry.get().strip())
            entry.destroy()

        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def _set_layer_name(self, key: str, row: str, value: str) -> None:
        if not value:
            return
        getattr(self._config, key).name = value
        self._layer_tree.set(row, "name", value)

    def _set_linetype(self, key: str, row: str, value: str) -> None:
        if not value:
            return
        getattr(self._config, key).linetype = value
        self._layer_tree.set(row, "linetype", value)

    def _pick_color(self, key: str, row: str) -> None:
        style: LayerStyle = getattr(self._config, key)
        ColorPickerPopup(self, style, on_change=lambda c: self._apply_color(key, row, c))

    def _apply_color(self, key: str, row: str, aci: int) -> None:
        getattr(self._config, key).color = aci
        self._layer_tree.set(row, "color", ACI_BY_VALUE.get(aci, str(aci)))

    # ---------------- 탭2: 크기 ----------------
    def _build_sizes_tab(self):
        frame = self._tab_sizes

        # ── 축척 프리셋 ──
        ttk.Label(frame, text="축척 프리셋").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self._preset_var = tk.StringVar(value=self._config.scale_preset)
        preset_combo = ttk.Combobox(
            frame, textvariable=self._preset_var, width=24,
            values=[p.label for p in SCALE_PRESETS], state="readonly",
        )
        preset_combo.grid(row=0, column=1, padx=8, pady=4, sticky="w")
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)
        # 프리셋 설명
        ttk.Label(
            frame, text="(프리셋 선택 시 축척과 크기가 자동 설정)",
            foreground="gray",
        ).grid(row=0, column=2, columnspan=2, sticky="w", padx=4)

        # ── 표시 옵션 ──
        opts = ttk.LabelFrame(frame, text="표시 옵션")
        opts.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=6)

        # ── IP 블록 타입 ──
        ttk.Label(opts, text="IP 제원표 블록 타입").grid(
            row=0, column=0, sticky="w", padx=6, pady=2,
        )
        initial_label = _TYPE_LABEL_MAP.get(self._config.ip_block_type, "기본 (1:1000 실시설계)")
        self._var_ip_block_label = tk.StringVar(value=initial_label)
        ttk.Combobox(
            opts, textvariable=self._var_ip_block_label, width=26, state="readonly",
            values=list(_TYPE_ID_BY_LABEL.keys()),
        ).grid(row=0, column=1, columnspan=2, sticky="w", padx=6, pady=2)

        # ── 곡선제원문자 표시 ──
        self._var_show_curve = tk.BooleanVar(value=self._config.show_curve_label)
        ttk.Checkbutton(opts, text="곡선제원문자 표시", variable=self._var_show_curve).grid(
            row=0, column=3, sticky="w", padx=6, pady=2,
        )

        # ── 곡선 문자 모드 ──
        ttk.Label(opts, text="곡선 문자 모드").grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self._var_label_mode = tk.StringVar(value=self._config.curve_label_mode)
        ttk.Radiobutton(opts, text="전체 (라벨=측점)", value="full",
                        variable=self._var_label_mode).grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(opts, text="라벨만 (SP/PC/CP/PS)", value="label_only",
                        variable=self._var_label_mode).grid(row=1, column=2, sticky="w")

        # show_sub_text, show_km_text 체크박스로 (기존 show_200_text → show_sub_text로 이름 변경)
        # ── 200m/km 문자 ──
        self._var_show_sub  = tk.BooleanVar(value=self._config.show_sub_text)
        ttk.Checkbutton(opts, text="200m 문자 표시",
                        variable=self._var_show_sub).grid(row=2, column=0, sticky="w", padx=6, pady=2)

        self._var_show_km  = tk.BooleanVar(value=self._config.show_km_text)
        ttk.Checkbutton(opts, text="km 문자 표시",
                        variable=self._var_show_km).grid(row=2, column=1, sticky="w", padx=6, pady=2)
        # ── 기존 크기 필드들 (row 2부터) ──
        base = 2
        for i, (key, label) in enumerate(_SIZE_FIELDS):
            row = base + i
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=3)
            var = tk.StringVar(value=str(getattr(self._config, key)))
            ttk.Entry(frame, textvariable=var, width=12).grid(row=row, column=1, padx=8, pady=3, sticky="w")
            self._size_vars[key] = var

        base2 = base + len(_SIZE_FIELDS)
        ttk.Separator(frame, orient="horizontal").grid(
            row=base2, column=0, columnspan=3, sticky="ew", pady=6,
        )
        # ── 측점 표시 ──
        ttk.Label(frame, text="주 심볼 간격 (m)").grid(row=base2 + 1, column=0, sticky="w", padx=8, pady=3)
        self._main_tick_var = tk.StringVar(value=str(self._config.main_tick))
        ttk.Entry(frame, textvariable=self._main_tick_var , width=12).grid(
            row=base2 + 1, column=1, padx=8, pady=3, sticky="w",
        )

        ttk.Label(frame, text="보조 심볼 간격 (m, 0=비활성)").grid(row=base2 + 2, column=0, sticky="w", padx=8, pady=3)
        self._sub_symbol_var  = tk.StringVar(value=str(self._config.sub_symbol))
        ttk.Entry(frame, textvariable=self._sub_symbol_var , width=12).grid(
            row=base2 + 2, column=1, padx=8, pady=3, sticky="w",
        )

        ttk.Label(frame, text="보조 틱 간격 (m, 0=비활성)").grid(row=base2 + 3, column=0, sticky="w", padx=8, pady=3)
        self._sub_tick_var  = tk.StringVar(value=str(self._config.sub_tick))
        ttk.Entry(frame, textvariable=self._sub_tick_var, width=12).grid(
            row=base2 + 3, column=1, padx=8, pady=3, sticky="w",
        )

        ttk.Label(frame, text="km 소수 자리수").grid(row=base2 + 4, column=0, sticky="w", padx=8, pady=3)
        self._km_precision_var = tk.StringVar(value=str(self._config.km_precision))
        ttk.Spinbox(frame, from_=0, to=4, textvariable=self._km_precision_var, width=10).grid(
            row=base2 + 4, column=1, padx=8, pady=3, sticky="w",
        )

    def _on_preset_selected(self, _e=None):
        """프리셋 선택 시 값 제안."""
        label = self._preset_var.get()
        preset = next((p for p in SCALE_PRESETS if p.label == label), None)
        if not preset:
            return
        self._config = apply_preset_to_config(self._config, preset)
        self._refresh_all()

    # ---------------- 탭3: 프리셋 ----------------
    def _build_preset_tab(self) -> None:
        frame = self._tab_preset
        ttk.Button(frame, text="기본값으로 복원", command=self._restore_default).pack(fill="x", padx=8, pady=8)
        ttk.Button(frame, text="프리셋 불러오기...", command=self._load_preset).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="프리셋 저장...", command=self._save_preset).pack(fill="x", padx=8, pady=4)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=8, pady=12)

        ttk.Button(frame, text="자동 저장 위치에 지금 저장", command=self._save_default).pack(fill="x", padx=8, pady=4)
        ttk.Label(
            frame,
            text="기본 저장 위치: ~/.railway_alignment/dxf_config.json\n"
                 "(앱 종료 후에도 유지됩니다)",
            foreground="gray", justify="left",
        ).pack(fill="x", padx=8, pady=(4, 12))

    def _restore_default(self) -> None:
        if not messagebox.askyesno("확인", "기본값으로 복원하시겠습니까?", parent=self):
            return
        self._config = DXFConfig()
        self._refresh_all()

    def _load_preset(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="프리셋 불러오기",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self._config = DXFConfig.load(Path(path))
            self._refresh_all()
        except Exception as e:
            messagebox.showerror("오류", f"프리셋을 읽을 수 없습니다: {e}", parent=self)

    def _save_preset(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="프리셋 저장",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        self._collect_values()
        try:
            self._config.save(Path(path))
            messagebox.showinfo("완료", f"저장되었습니다:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}", parent=self)

    def _save_default(self) -> None:
        self._collect_values()
        try:
            path = self._config.save()   # 기본 경로
            messagebox.showinfo("완료", f"자동 저장 위치에 저장되었습니다:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}", parent=self)

    # ---------------- 값 수집 / 반영 ----------------
    def _collect_values(self):
        # 기존 크기 필드
        for key, var in self._size_vars.items():
            try:
                setattr(self._config, key, float(var.get()))
            except ValueError:
                pass

        # 간격 필드
        try:
            self._config.km_interval = int(self._main_tick_var.get())
        except ValueError:
            pass
        try:
            self._config.sym200_interval = int(self._sub_symbol_var.get())
        except ValueError:
            pass
        try:
            self._config.unit_floor = int(self._sub_tick_var.get())
        except ValueError:
            pass
        try:
            self._config.km_precision = int(self._km_precision_var.get())
        except ValueError:
            pass

        # 표시 옵션
        label = self._var_ip_block_label.get()
        self._config.ip_block_type = _TYPE_ID_BY_LABEL.get(label, "default")
        self._config.show_curve_label = self._var_show_curve.get()
        self._config.curve_label_mode = self._var_label_mode.get()
        self._config.show_200_text = self._var_show_sub.get()
        self._config.show_km_text = self._var_show_km.get()
        self._config.scale_preset = self._preset_var.get()

    def _refresh_all(self) -> None:
        # 레이어 탭 갱신
        for key, label in _LAYER_FIELDS:
            iid = self._layer_rows[key]
            lyr: LayerStyle = getattr(self._config, key)
            self._layer_tree.set(iid, "name", lyr.name)
            self._layer_tree.set(iid, "color", ACI_BY_VALUE.get(lyr.color, str(lyr.color)))
            self._layer_tree.set(iid, "linetype", lyr.linetype)

        # 크기 탭 갱신
        for key, var in self._size_vars.items():
            var.set(str(getattr(self._config, key)))
        self._main_tick_var.set(str(self._config.main_tick))
        self._sub_symbol_var.set(str(self._config.sub_symbol))
        self._sub_tick_var.set(str(self._config.sub_tick))
        self._km_precision_var.set(str(self._config.km_precision))

        # 표시 옵션
        label = _TYPE_LABEL_MAP.get(self._config.ip_block_type, "기본 (1:1000 실시설계)")    # ✅
        self._var_ip_block_label.set(label)
        self._var_show_curve.set(self._config.show_curve_label)
        self._var_label_mode.set(self._config.curve_label_mode)
        self._var_show_sub.set(self._config.show_sub_text)
        self._var_show_km.set(self._config.show_km_text)
        self._preset_var.set(self._config.scale_preset)

    # ---------------- 적용 ----------------
    def _on_apply_clicked(self) -> None:
        self._collect_values()

        # 미구현 블록 타입 경고
        if self._config.ip_block_type not in IMPLEMENTED_BLOCK_TYPES:
            label = _TYPE_LABEL_MAP.get(self._config.ip_block_type, self._config.ip_block_type)
            if not messagebox.askyesno(
                    "미구현 블록 타입",
                    f"'{label}'은 아직 구현되지 않았습니다.\n"
                    f"DXF 출력 시 오류가 발생합니다. 계속하시겠습니까?",
                    parent=self,
            ):
                return

        try:
            self._config.save()
        except Exception:
            logger.exception("기본 경로 저장 실패 (무시)")

        if self._on_apply is not None:
            try:
                self._on_apply(self._config)
            except Exception:
                logger.exception("on_apply 콜백 오류")

        self.destroy()


# ============================================================
# 색상 선택 팝업 (ACI)
# ============================================================
class ColorPickerPopup(tk.Toplevel):
    """ACI 색상 선택 팝업."""

    def __init__(self, master, style: LayerStyle, on_change: Callable[[int], None]):
        super().__init__(master)
        self.title("색상 선택")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        self._on_change = on_change

        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="both", expand=True)

        for i, (aci, name) in enumerate(ACI_COLORS):
            text = f"{aci}  {name}" + ("  ✓" if aci == style.color else "")
            ttk.Button(
                frame, text=text, width=20,
                command=lambda a=aci: self._choose(a),
            ).grid(row=i, column=0, pady=2, sticky="ew")

        ttk.Button(frame, text="취소", command=self.destroy).grid(
            row=len(ACI_COLORS), column=0, pady=(8, 0), sticky="ew",
        )

    def _choose(self, aci: int) -> None:
        self._on_change(aci)
        self.destroy()

