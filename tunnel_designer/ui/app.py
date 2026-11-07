"""TunnelApp — 전체 오케스트레이션."""
from __future__ import annotations
import math
from dataclasses import replace
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from core.constants import (
    TunnelType, CornerStyle,
    DXF_DEFAULT_IN, MIN_PILLAR_W,
    HATCH_STYLE_SOLID, LEFT_PANEL_WIDTH,
)
from core.models import (
    TunnelParams, ArchParams, FitHistoryEntry, SnapshotEntry, TrackParams,
)
from core.geometry import (
    compute_geometry_from_arch, compute_fl, fit_R1_Y_to_FL,
    compute_multi_arch, check_multi_arch_overlap,
    align_multi_arch_fl, compute_box_geometry,
)
from services.history import FitHistory
from services.snapshot import SnapshotStore
from services.dxf_io import DxfCache, write_dxf
from render.drawing import (
    draw_cad, draw_single_natm, draw_multi_arch, draw_box,
    spec_single_natm, spec_multi_arch, spec_box, draw_clearance_overlay,
)
from ui.style import setup_style
from ui.dialogs import ask_reference_arch, confirm_align_dialog
from ui.panels import ControlsPanel, CanvasPanel


class TunnelApp:
    def __init__(self):
        self.params = TunnelParams()
        self.dxf = DxfCache()
        self.dxf_path = DXF_DEFAULT_IN
        self.history = FitHistory()
        self.snapshots = SnapshotStore()
        self._suspend = False

        self.root = tk.Tk()
        self.root.title("터널 단면 작도기 v6")
        self.root.geometry("1380x960")
        self.root.minsize(1180, 820)
        setup_style(self.root)

        self.auto_avoid_overlap = tk.BooleanVar(value=False)
        self.hatch_style = tk.StringVar(value=HATCH_STYLE_SOLID)

        # ✅ 교체: Frame + pack으로 폭 완전 고정
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(main, padding=(4, 4), width=LEFT_PANEL_WIDTH)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)  # ★ 자식이 폭 강제 확장하지 못하게 함

        right = ttk.Frame(main, padding=(4, 4))
        right.pack(side="left", fill="both", expand=True)

        self.controls = ControlsPanel(left, self)
        self.canvas_panel = CanvasPanel(right, self)
        self.ax = self.canvas_panel.ax
        self.canvas = self.canvas_panel.canvas

        self.update_plot()
        self._bind_shortcuts()

    # ── 단축키 ────────────────────────────────────
    def _bind_shortcuts(self):
        r = self.root
        r.bind("<Control-s>", lambda e: self.save_dxf())
        r.bind("<Control-o>", lambda e: self.open_dxf())
        r.bind("<Control-f>", lambda e: self.auto_fit_fl())
        r.bind("<Control-Shift-F>", lambda e: self._shortcut_align())
        r.bind("<Control-Shift-S>", lambda e: self.take_snapshot())

    def _shortcut_align(self):
        if self.params.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            self.align_multi_arch_fl_ui()
        else:
            messagebox.showinfo(
                "FL 통일",
                "다중 아치(2-Arch / 3-Arch)에서만 사용할 수 있습니다.")

    # ── 파라미터 콜백 ──────────────────────────────
    def on_param_change(self, attr: str, value: float):

        if self._suspend:
            return
        setattr(self.params, attr, value)
        if self._maybe_auto_avoid():
            return
        self.update_plot()

    def on_track_param_change(self, key: str, value: float):
        """key 형식: 'track_0.offset_x'"""
        if self._suspend:
            return
        _, attr = key.split(".", 1)
        idx = int(key.split("_")[1].split(".")[0])
        tracks = self.params.get_tracks()

        # ★ tracks를 실체화 (비어있으면 D 기반 2트랙 채움)
        if not self.params.tracks:
            self.params.tracks = tracks

        if 0 <= idx < len(self.params.tracks):
            setattr(self.params.tracks[idx], attr, value)
            self.update_plot()

    def on_track_label_change(self, idx: int, label: str):
        tracks = self.params.get_tracks()
        if not self.params.tracks:
            self.params.tracks = tracks
        if 0 <= idx < len(self.params.tracks):
            self.params.tracks[idx].label = label
            self.update_plot()

    def on_arch_param_change(self, key: str, value: float):
        if self._suspend:
            return
        i_str, attr = key.split(".", 1)
        idx = int(i_str.replace("arch", ""))
        setattr(self.params.arches[idx], attr, value)
        if self._maybe_auto_avoid():
            return
        self.update_plot()

    def on_box_style_change(self):
        self.params.box_style_top = CornerStyle(
            self.style_top_var.get())
        self.params.box_style_bot = CornerStyle(
            self.style_bot_var.get())
        self.update_plot()

    def on_type_change(self):
        new_kind = TunnelType(self.type_var.get())
        if new_kind == self.params.kind:
            return
        self.params.kind = new_kind

        if (new_kind == TunnelType.NATM_2ARCH
                and len(self.params.arches) != 2):
            a = ArchParams(R1=self.params.R1,
                            top_angle=self.params.top_angle,
                            R2=self.params.R2,
                            r2_angle=self.params.r2_angle,
                            R1_Y=self.params.R1_Y)
            self.params.arches = [replace(a, label="좌선"),
                                   replace(a, label="우선")]
        elif (new_kind == TunnelType.NATM_3ARCH
              and len(self.params.arches) != 3):
            central = ArchParams(R1=9.0, top_angle=100.0, R2=7.0,
                                 r2_angle=70.0, R1_Y=2.0, label="중앙")
            side = ArchParams(R1=5.5, top_angle=85.0, R2=4.5,
                              r2_angle=65.0, R1_Y=1.5, label="측선")
            self.params.arches = [central,
                                   replace(side, label="좌선"),
                                   replace(side, label="우선")]

        self.controls.populate()
        self._update_action_buttons(new_kind)
        self.update_plot()

    def _update_action_buttons(self, kind):
        if kind == TunnelType.NATM:
            self.btn_auto_fit.grid()
        else:
            self.btn_auto_fit.grid_remove()
        if kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            self.btn_align_fl.grid()
        else:
            self.btn_align_fl.grid_remove()

    # ── 자동 겹침 회피 ────────────────────────────
    def _maybe_auto_avoid(self) -> bool:
        if (not self.auto_avoid_overlap.get()
                or self.params.kind not in (TunnelType.NATM_2ARCH,
                                             TunnelType.NATM_3ARCH)):
            return False
        return self._auto_fix_overlap()

    def _auto_fix_overlap(self) -> bool:
        fixed = False
        for _ in range(10):
            mg = compute_multi_arch(self.params)
            info = check_multi_arch_overlap(mg)
            if not info.has_overlap:
                break
            need = -info.min_gap + 0.01
            if self.params.kind == TunnelType.NATM_2ARCH:
                self.params.pillar_w += need
                self._suspend = True
                try:
                    if "pillar_w" in self.controls.rows:
                        self.controls.rows["pillar_w"].set_value(
                            self.params.pillar_w)
                finally:
                    self._suspend = False
            else:
                self.params.gap_L += need / 2
                self.params.gap_R += need / 2
                self._suspend = True
                try:
                    for k in ("gap_L", "gap_R"):
                        if k in self.controls.rows:
                            self.controls.rows[k].set_value(
                                getattr(self.params, k))
                finally:
                    self._suspend = False
            fixed = True
        if fixed:
            self.update_plot()
        return fixed

    # ── 파라미터 일괄 적용 ────────────────────────
    def _apply_params(self, **kwargs):
        self._suspend = True
        try:
            for k, v in kwargs.items():
                if not hasattr(self.params, k):
                    continue
                setattr(self.params, k, v)
                if k in self.controls.rows:
                    self.controls.rows[k].set_value(v)
        finally:
            self._suspend = False
        self.update_plot()

    def reset_params(self):
        if not messagebox.askyesno("초기값 복원",
                                    "모든 파라미터를 초기값으로 되돌릴까요?"):
            return
        kind = self.params.kind
        d = TunnelParams(kind=kind)
        if kind == TunnelType.NATM_2ARCH:
            a = ArchParams()
            d.arches = [replace(a, label="좌선"),
                        replace(a, label="우선")]
        elif kind == TunnelType.NATM_3ARCH:
            central = ArchParams(R1=9.0, top_angle=100.0, R2=7.0,
                                  r2_angle=70.0, R1_Y=2.0, label="중앙")
            side = ArchParams(R1=5.5, top_angle=85.0, R2=4.5,
                               r2_angle=65.0, R1_Y=1.5, label="측선")
            d.arches = [central, replace(side, label="좌선"),
                        replace(side, label="우선")]
        self.params = d
        self.type_var.set(kind.value)
        self.controls.populate()
        self._update_action_buttons(kind)
        self.update_plot()

    # ── FL 자동 맞춤 ──────────────────────────────
    def auto_fit_fl(self):
        if self.params.kind != TunnelType.NATM:
            if self.params.kind == TunnelType.BOX:
                messagebox.showinfo("FL 자동 맞춤",
                                     "개착 Box형은 H가 FL을 직접 결정합니다.")
            else:
                messagebox.showinfo(
                    "FL 자동 맞춤",
                    "2-Arch / 3-Arch는 '아치 FL 통일'을 사용하세요.\n"
                    "(Ctrl+Shift+F)")
            return

        p = self.params
        target = simpledialog.askfloat(
            "FL 자동 맞춤",
            f"목표 FL 값을 입력하세요 (현재 {p.FL:.3f}):",
            initialvalue=p.FL)
        if target is None:
            return

        p_target = replace(p, FL=target)
        r1_y_prev = p.R1_Y
        r1_y_opt, ok = fit_R1_Y_to_FL(p_target)

        if not ok:
            self.history.add(p_target, r1_y_prev, float("nan"),
                             success=False)
            self._refresh_history_view()
            messagebox.showwarning(
                "자동 맞춤 실패",
                f"FL={target}을 만족하는 R1_Y를 찾을 수 없습니다.")
            return

        self.params.FL = target
        self.params.R1_Y = r1_y_opt
        self._suspend = True
        try:
            self.controls.rows["FL"].set_value(target)
            self.controls.rows["R1_Y"].set_value(r1_y_opt)
        finally:
            self._suspend = False
        self.update_plot()

        achieved = compute_fl(self.params, r1_y_opt)
        entry = self.history.add(self.params, r1_y_prev, achieved,
                                  success=True)
        self._refresh_history_view()
        self.take_snapshot(auto=True,
                            note=f"NATM FL 자동 맞춤 (목표 {target:.3f})")

        messagebox.showinfo(
            "자동 맞춤 완료",
            f"R1_Y  = {r1_y_opt:.4f}  (Δ {entry.dR1_Y:+.4f})\n"
            f"FL     = {achieved:.4f}  (목표 {target})\n"
            f"이력 {len(self.history.entries)}건 / "
            f"스냅샷 {len(self.snapshots.entries)}건")

    # ── FL 통일 (다중 아치) ──────────────────────
    def align_multi_arch_fl_ui(self):
        if self.params.kind not in (TunnelType.NATM_2ARCH,
                                     TunnelType.NATM_3ARCH):
            return
        p = self.params
        labels = [a.label for a in p.arches]

        ref_idx = ask_reference_arch(self.root, labels, 0)
        if ref_idx is None:
            return

        result = align_multi_arch_fl(p, reference_idx=ref_idx)
        if not all(result.success):
            fails = [labels[i] for i, ok in enumerate(result.success)
                     if not ok]
            messagebox.showwarning(
                "FL 통일 실패",
                f"다음 아치의 FL을 맞출 수 없습니다: {', '.join(fails)}\n"
                f"R1/R2/각도 조합을 확인하세요.")
            return

        if not confirm_align_dialog(self.root, result, labels[ref_idx]):
            return
        if not self._guard_overlap("FL 통일 적용"):
            return

        self._suspend = True
        try:
            for i, new_y in enumerate(result.new_R1Y):
                self.params.arches[i] = replace(
                    self.params.arches[i], R1_Y=new_y)
            for i, rows in enumerate(self.controls.arch_rows):
                if "R1_Y" in rows:
                    rows["R1_Y"].set_value(result.new_R1Y[i])
        finally:
            self._suspend = False

        self.update_plot()
        self.take_snapshot(auto=True,
                            note=f"FL 통일 후 (기준: {labels[ref_idx]}, "
                                 f"FL={result.target_FL:.3f})")

        messagebox.showinfo(
            "FL 통일 완료",
            f"기준: {labels[ref_idx]}  (FL = {result.target_FL:.4f} m)\n"
            + "\n".join(
                f"  {result.labels[i]}: R1_Y {result.old_R1Y[i]:.3f} → "
                f"{result.new_R1Y[i]:.3f}  "
                f"(Δ {result.new_R1Y[i] - result.old_R1Y[i]:+.3f})"
                for i in range(len(result.labels))))

    def _guard_overlap(self, action_name: str) -> bool:
        if self.params.kind not in (TunnelType.NATM_2ARCH,
                                     TunnelType.NATM_3ARCH):
            return True
        mg = compute_multi_arch(self.params)
        info = check_multi_arch_overlap(mg)
        if not info.has_overlap:
            return True
        names = [f"{mg.layout[i].label}↔{mg.layout[j].label}"
                 for i, j in info.pairs]
        total = sum(info.overlap_areas)
        return messagebox.askyesno(
            "아치 겹침 경고",
            f"다음 아치가 겹쳐 있습니다:\n  {', '.join(names)}\n"
            f"겹침 면적 합: {total:.2f}㎡\n\n"
            f"그래도 {action_name}을(를) 계속할까요?")

    # ── 이력 ─────────────────────────────────────
    def _refresh_history_view(self):
        tree = self.canvas_panel.hist_tree
        for i in tree.get_children():
            tree.delete(i)
        for e in self.history.entries:
            status = "✅" if e.is_ok else ("⚠️" if e.success else "❌")
            tree.insert("", "end", values=(
                e.timestamp, f"{e.target_FL:.4f}",
                f"{e.achieved_FL:.4f}" if e.success else "-",
                f"{e.R1_Y:.4f}", f"{e.dR1_Y:+.4f}",
                f"{e.R1:.2f}", f"{e.top_angle:.1f}",
                f"{e.R2:.2f}", f"{e.r2_angle:.1f}", f"{e.D:.2f}",
                status))
        self.canvas_panel.hist_count.config(
            text=f"{len(self.history.entries)}건")

    def on_history_dblclick(self, _evt):
        tree = self.canvas_panel.hist_tree
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        e = self.history.entries[idx]
        if not messagebox.askyesno(
                "이력 복원",
                f"{e.timestamp} 값으로 파라미터를 복원할까요?"):
            return
        if self.params.kind != TunnelType.NATM:
            self.type_var.set(TunnelType.NATM.value)
            self.params.kind = TunnelType.NATM
            self.controls.populate()
            self._update_action_buttons(TunnelType.NATM)
        self._apply_params(R1=e.R1, top_angle=e.top_angle, R2=e.R2,
                            r2_angle=e.r2_angle, D=e.D,
                            R1_Y=e.R1_Y, FL=e.target_FL)

    def save_history_csv(self):
        if not self.history.entries:
            messagebox.showinfo("이력", "저장할 이력이 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            title="이력 CSV 저장", defaultextension=".csv",
            initialfile=f"fit_history_{datetime.now():%Y%m%d_%H%M%S}.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            self.history.to_csv(path)
            messagebox.showinfo("저장 완료", path)
        except Exception as ex:
            messagebox.showerror("저장 실패", str(ex))

    def clear_history(self):
        if not self.history.entries:
            return
        if messagebox.askyesno(
                "이력 초기화",
                f"{len(self.history.entries)}건을 삭제할까요?"):
            self.history.entries.clear()
            self._refresh_history_view()

    # ── 스냅샷 ──────────────────────────────────
    def take_snapshot(self, auto: bool = False, note: str = ""):
        if not auto and not self._guard_overlap("스냅샷 저장"):
            return
        p = self.params
        if p.kind == TunnelType.BOX:
            total = compute_box_geometry(p).inner_area
        elif p.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            total = compute_multi_arch(p).total_area
        else:
            a = ArchParams(R1=p.R1, top_angle=p.top_angle, R2=p.R2,
                            r2_angle=p.r2_angle, R1_Y=p.R1_Y, cx=0.0)
            total = compute_geometry_from_arch(a, FL=p.FL).area

        if not auto:
            note = simpledialog.askstring(
                "제원 스냅샷", "메모를 입력하세요 (선택):",
                initialvalue=note or p.kind.value) or ""

        self.snapshots.add(p, total_area=total, note=note)
        self._refresh_snapshot_view()
        if not auto:
            messagebox.showinfo(
                "스냅샷 저장",
                f"제원 스냅샷이 저장되었습니다 "
                f"({len(self.snapshots.entries)}건).")

    def _refresh_snapshot_view(self):
        tree = self.canvas_panel.snap_tree
        for i in tree.get_children():
            tree.delete(i)
        for e in self.snapshots.entries:
            tree.insert("", "end", values=(
                e.timestamp, e.kind, f"{e.total_area:.2f}", e.note))
        self.canvas_panel.snap_count.config(
            text=f"{len(self.snapshots.entries)}건")

    def on_snapshot_dblclick(self, _evt):
        tree = self.canvas_panel.snap_tree
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        e = self.snapshots.entries[idx]
        if not messagebox.askyesno(
                "스냅샷 복원",
                f"{e.timestamp}\n{e.kind}\n{e.note or '(메모 없음)'}\n\n"
                f"이 제원으로 복원할까요?"):
            return
        self._restore_snapshot(e)

    def _restore_snapshot(self, e: SnapshotEntry):
        try:
            new_p = SnapshotStore.deserialize(e.payload)
        except Exception as ex:
            messagebox.showerror("복원 실패", str(ex))
            return
        self.params = new_p
        self.type_var.set(new_p.kind.value)
        self.controls.populate()
        self._update_action_buttons(new_p.kind)
        self.update_plot()

    def delete_snapshot(self):
        tree = self.canvas_panel.snap_tree
        sel = tree.selection()
        if not sel:
            return
        idxs = sorted((tree.index(i) for i in sel), reverse=True)
        if not messagebox.askyesno("삭제",
                                    f"{len(idxs)}건을 삭제할까요?"):
            return
        for i in idxs:
            self.snapshots.entries.pop(i)
        self._refresh_snapshot_view()

    def clear_snapshots(self):
        if not self.snapshots.entries:
            return
        if messagebox.askyesno(
                "스냅샷 초기화",
                f"{len(self.snapshots.entries)}건을 삭제할까요?"):
            self.snapshots.entries.clear()
            self._refresh_snapshot_view()

    def save_snapshots_json(self):
        if not self.snapshots.entries:
            messagebox.showinfo("스냅샷", "저장할 스냅샷이 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            title="스냅샷 JSON 저장", defaultextension=".json",
            initialfile=f"snapshots_{datetime.now():%Y%m%d_%H%M%S}.json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            self.snapshots.to_json(path)
            messagebox.showinfo("저장 완료", path)
        except Exception as ex:
            messagebox.showerror("저장 실패", str(ex))

    def load_snapshots_json(self):
        path = filedialog.askopenfilename(
            title="스냅샷 JSON 불러오기",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.snapshots.from_json(path)
            self._refresh_snapshot_view()
            messagebox.showinfo(
                "불러오기 완료",
                f"{len(self.snapshots.entries)}건 로드됨.")
        except Exception as ex:
            messagebox.showerror("불러오기 실패", str(ex))

    # ── 렌더링 ──────────────────────────────────
    def update_plot(self):
        p = self.params
        ax = self.ax
        ax.clear()
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, color="#e5e5e5", linewidth=0.6)

        # ✅ 트랙별 차량한계선 개별 표시
        ents = self.dxf.load(self.dxf_path)
        draw_clearance_overlay(ax, ents, p)

        if p.kind == TunnelType.BOX:
            g = compute_box_geometry(p)
            draw_box(ax, g)
            self.controls.spec_label.config(text=spec_box(g))
        elif p.kind in (TunnelType.NATM_2ARCH, TunnelType.NATM_3ARCH):
            mg = compute_multi_arch(p)
            draw_multi_arch(ax, mg, p)
            self.controls.spec_label.config(text=spec_multi_arch(mg, p))
        else:
            a = ArchParams(R1=p.R1, top_angle=p.top_angle, R2=p.R2,
                            r2_angle=p.r2_angle, R1_Y=p.R1_Y,
                            cx=0.0, label="본선")
            # ★ 라이닝 파라미터 전달
            g = compute_geometry_from_arch(
                a, FL=p.FL,
                ts=p.ts, ts_slab=p.ts_slab, show_lining=p.show_lining
            )
            draw_single_natm(ax, g, p)
            self.controls.spec_label.config(text=spec_single_natm(g, p))

        self.canvas.draw_idle()

    # ── DXF ────────────────────────────────────
    def open_dxf(self):
        path = filedialog.askopenfilename(
            title="DXF 파일 선택",
            filetypes=[("DXF", "*.dxf"), ("All files", "*.*")])
        if not path:
            return
        self.dxf_path = path
        if self.dxf.load(path, force=True) is not None:
            self.update_plot()

    def save_dxf(self):
        if not self._guard_overlap("DXF 저장"):
            return
        path = filedialog.asksaveasfilename(
            title="DXF 저장", defaultextension=".dxf",
            initialfile="TUNNEL_output.dxf",
            filetypes=[("DXF", "*.dxf")])
        if not path:
            return
        try:
            write_dxf(path, self.ax, self.params, self.hatch_style.get())
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))
            return

        overlap_note = ""
        if self.params.kind in (TunnelType.NATM_2ARCH,
                                 TunnelType.NATM_3ARCH):
            mg = compute_multi_arch(self.params)
            info = check_multi_arch_overlap(mg)
            if info.has_overlap:
                overlap_note = (
                    f"\n\n⚠ 겹침 {len(info.pairs)}개소가 "
                    f"OVERLAP 레이어 HATCH로 포함되었습니다.")
        messagebox.showinfo("저장 완료", path + overlap_note)

    # ── 종료 ──────────────────────────────────
    def close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()

    def add_track(self):
        tracks = self.params.get_tracks()
        if not self.params.tracks:
            self.params.tracks = tracks
        if len(self.params.tracks) >= 2:
            last = self.params.tracks[-1].offset_x
            prev = self.params.tracks[-2].offset_x
            spacing = last - prev
        else:
            spacing = 2.0
        new_x = (self.params.tracks[-1].offset_x if self.params.tracks
                 else 0.0) + max(spacing, 1.0)
        self.params.tracks.append(
            TrackParams(offset_x=new_x, label=f"T{len(self.params.tracks) + 1}",
                        show_clearance=True))
        self.controls.populate()
        self.update_plot()

    def remove_track(self, idx: int):
        tracks = self.params.get_tracks()
        if not self.params.tracks:
            self.params.tracks = tracks
        if len(self.params.tracks) <= 1:
            return
        if not messagebox.askyesno("트랙 삭제",
                                   f"{idx + 1}번 트랙을 삭제할까요?"):
            return
        self.params.tracks.pop(idx)
        self.controls.populate()
        self.update_plot()

    def reset_tracks_to_D(self):
        """D 기반 2트랙(하선/상선)으로 초기화."""
        if not messagebox.askyesno("초기화",
                                   "선로를 D 기반 2트랙으로 되돌릴까요?"):
            return
        self.params.tracks.clear()
        self.controls.populate()
        self.update_plot()

    def on_track_clearance_toggle(self, idx: int, enabled: bool):
        tracks = self.params.get_tracks()
        if not self.params.tracks:
            self.params.tracks = tracks
        if 0 <= idx < len(self.params.tracks):
            self.params.tracks[idx].show_clearance = enabled
            self.update_plot()