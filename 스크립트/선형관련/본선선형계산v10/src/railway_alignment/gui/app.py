"""
메인 윈도우 (패널 통합)
========================
패널 기반 선형편집도구. 서비스(AlignmentService)는 단일 진실 공급원.

규칙:
    - 편집 중 재계산은 calculate_only() (파일 저장 없음)
    - "계산+저장" 버튼만 calculate() 호출
    - 검증 결과는 result.issues(ValidationIssue)에서 읽음
    - 미리보기 선형 좌표는 result.polycurve
    - 외부 콜백 인자는 ip_no(1-based)로 통일
    - raw_lines 인덱스 == ip_no (raw_lines[0]=BP)
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from typing import Optional

from src.railway_alignment.core.constants import Config
from src.railway_alignment.core.math_util import format_station
from src.railway_alignment.core.validator import issues_by_ip as group_issues_by_ip
from src.railway_alignment.io.parsers import read_alignment_file
from src.railway_alignment.io.project_io import PROJECT_EXTENSION, PROJECT_FILETYPES, save_project, add_recent_project, \
    ProjectIOError, load_recent_projects, clear_recent_projects, load_project, ProjectData
from src.railway_alignment.service.alignment_service import (
    AlignmentInput,
    AlignmentResult,
    AlignmentService,
    AlignmentServiceError,
)

from src.railway_alignment.gui.preview_canvas import PreviewCanvas
from src.railway_alignment.gui.ip_table import IPTableEditor
from src.railway_alignment.gui.validator_panel import ValidatorPanel
from src.railway_alignment.gui.dxf_settings_dialog import DXFSettingsDialog
from src.railway_alignment.io.dxf_config import DXFConfig, apply_preset_to_config

logger = logging.getLogger(__name__)


class MainWindow:
    """패널 기반 선형편집도구 메인 윈도우."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Railway Alignment Tool — 선형편집도구")
        self.root.geometry("1600x820")

        self.service = AlignmentService()

        self._raw_lines: Optional[list[list[str]]] = None
        self._result: Optional[AlignmentResult] = None
        self._current_file: Optional[str] = None

        self._build_ui()
        self.root.after(100, self._on_open_file)

        self._current_project: Optional[str] = None  # 현재 프로젝트 파일
        self._auto_save_job = None  # after() id
        self._menu_recent = None  # 최근 메뉴 참조

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = self.root
        self._build_menubar()
        params = ttk.LabelFrame(root, text="계산 파라미터")
        params.pack(side="top", fill="x", padx=6, pady=(6, 2))

        self.entry_unit = self._labeled_entry(params, "계산 간격", "20", col=0)
        self.entry_start = self._labeled_entry(params, "시작 측점", "0", col=2)
        self.entry_speed = self._labeled_entry(params, "설계 속도", "250", col=4)

        ttk.Label(params, text="도상 유형").grid(row=0, column=6, padx=(12, 2))
        self.ballast_var = tk.IntVar(value=0)
        ttk.Radiobutton(params, text="자갈", variable=self.ballast_var, value=0).grid(
            row=0, column=7
        )
        ttk.Radiobutton(params, text="콘크리트", variable=self.ballast_var, value=1).grid(
            row=0, column=8
        )

        ttk.Button(params, text="파일 열기", command=self._on_open_file).grid(
            row=0, column=9, padx=(16, 4)
        )
        ttk.Button(params, text="재계산", command=self._on_recalculate).grid(
            row=0, column=10, padx=4
        )
        ttk.Button(params, text="계산+저장", command=self._on_calculate_and_save).grid(
            row=0, column=11, padx=4
        )
        ttk.Button(params, text="도면 설정", command=self._on_open_dxf_settings).grid(
            row=0, column=13, padx=(12, 4)
        )
        ttk.Button(params, text="도면 출력", command=self._on_export_dxf).grid(
            row=0, column=14, padx=4
        )

        center = ttk.PanedWindow(root, orient="horizontal")
        center.pack(side="top", fill="both", expand=True, padx=6, pady=4)

        left = ttk.Frame(center)
        center.add(left, weight=1)
        self.ip_table = IPTableEditor(
            left,
            on_edit=self._on_ip_edit,
            on_select=self._on_ip_select,
            on_insert=self._on_ip_insert,
            on_delete=self._on_ip_delete,
            on_auto_toggle=self._on_auto_toggle,
            on_type_toggle=self._on_type_toggle,  # ✅

        )
        self.ip_table.pack(fill="both", expand=True)

        right = ttk.PanedWindow(center, orient="vertical")
        center.add(right, weight=2)

        preview_frame = ttk.LabelFrame(right, text="평면 미리보기")
        right.add(preview_frame, weight=3)
        self.preview = PreviewCanvas(
            preview_frame, on_ip_click=self._on_preview_ip_click
        )
        self.preview.pack(fill="both", expand=True)

        validator_frame = ttk.LabelFrame(right, text="검증")
        right.add(validator_frame, weight=1)
        self.validator = ValidatorPanel(
            validator_frame,
            on_issue_select=self._on_issue_select,
            on_run_validate=self._on_recalculate,
        )
        self.validator.pack(fill="both", expand=True)

        bottom = ttk.Frame(root)
        bottom.pack(side="bottom", fill="x", padx=6, pady=6)

        ttk.Label(bottom, text="측점→좌표:").pack(side="left")
        self.entry_station = ttk.Entry(bottom, width=12)
        self.entry_station.pack(side="left", padx=(2, 2))
        ttk.Button(bottom, text="조회", command=self._on_lookup_coord).pack(
            side="left", padx=(0, 12)
        )

        ttk.Label(bottom, text="좌표→측점(x,y):").pack(side="left")
        self.entry_coord = ttk.Entry(bottom, width=20)
        self.entry_coord.pack(side="left", padx=(2, 2))
        ttk.Button(bottom, text="조회", command=self._on_lookup_station).pack(
            side="left", padx=(0, 12)
        )

        self.status_var = tk.StringVar(value="준비")
        ttk.Label(bottom, textvariable=self.status_var, foreground="gray").pack(
            side="right"
        )

    def _build_menubar(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="프로젝트 열기...", command=self._on_open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="프로젝트 저장", command=self._on_save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="프로젝트 다른 이름으로 저장...", command=self._on_save_project_as)
        file_menu.add_separator()

        self._menu_recent = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="최근 프로젝트", menu=self._menu_recent)
        self._refresh_recent_menu()
        file_menu.add_command(label="최근 목록 지우기", command=self._on_clear_recent)
        file_menu.add_separator()

        file_menu.add_command(label="TXT 데이터 열기...", command=self._on_open_file)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self._on_close)

        menubar.add_cascade(label="파일", menu=file_menu)
        self.root.config(menu=menubar)

        self.root.bind("<Control-o>", lambda e: self._on_open_project())
        self.root.bind("<Control-s>", lambda e: self._on_save_project())

    def _labeled_entry(
        self, parent: ttk.Widget, label: str, default: str, col: int
    ) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=0, column=col, padx=(6, 2))
        entry = ttk.Entry(parent, width=10)
        entry.insert(0, default)
        entry.grid(row=0, column=col + 1, padx=(0, 6))
        return entry

    # ------------------------------------------------------------------
    # 파라미터
    # ------------------------------------------------------------------
    def _read_inputs(self) -> AlignmentInput:
        def _int(entry: ttk.Entry, default: int) -> int:
            try:
                return int(entry.get())
            except (ValueError, tk.TclError):
                return default

        def _float(entry: ttk.Entry, default: float) -> float:
            try:
                return float(entry.get())
            except (ValueError, tk.TclError):
                return default

        return AlignmentInput(
            raw_lines=self._raw_lines or [],
            unit=_int(self.entry_unit, Config.DEFAULT_UNIT),
            start_sta=_float(self.entry_start, Config.DEFAULT_START_STA),
            design_speed=_int(self.entry_speed, Config.DEFAULT_DESIGN_SPEED),
            ballast="자갈도상" if self.ballast_var.get() == 0 else "콘크리트도상",
            parameter_overrides=self.ip_table.get_parameter_overrides(),  # ✅
            type_overrides=self.ip_table.get_type_overrides(),
        )

    # ------------------------------------------------------------------
    # 파일 열기
    # ------------------------------------------------------------------
    def _on_open_file(self) -> None:
        lines = read_alignment_file()
        if not lines:
            self.status_var.set("파일 선택 취소 또는 읽기 실패")
            return

        self._raw_lines = lines
        self._current_file = "(선택된 파일)"
        self._current_project = None  # ✅ TXT 열면 새 프로젝트
        self.status_var.set(f"파일 로드 완료: {len(lines)}행")

        self.ip_table.load_raw(lines)
        self._recalculate(save=False)

    # ------------------------------------------------------------------
    # 재계산
    # ------------------------------------------------------------------
    def _on_recalculate(self) -> None:
        self._recalculate(save=False)

    def _recalculate(self, save: bool) -> None:
        if not self._raw_lines:
            messagebox.showwarning("안내", "먼저 선형 데이터 파일을 열어주세요.")
            return

        self.validator.set_busy(True)
        self.status_var.set("계산 중...")
        self.root.update_idletasks()

        try:
            input_data = self._read_inputs()
            result = (
                self.service.calculate(input_data)
                if save
                else self.service.calculate_only(input_data)
            )

            self._result = result
            self.ip_table.load_curves(result.curves)
            self.ip_table.update_curve_columns(result.curves)
            self._refresh_preview()
            self._apply_validation(result)

            suffix = " (저장됨)" if save else ""
            self.status_var.set(
                f"계산 완료{suffix} — IP {len(result.curves)}개, "
                f"검증 {len(result.issues)}건"
            )
        except AlignmentServiceError as e:
            logger.error("계산 실패: %s", e)
            messagebox.showerror("Error", str(e))
            self.status_var.set("계산 실패")
        except Exception as e:
            logger.exception("예상치 못한 오류")
            messagebox.showerror("Error", f"예상치 못한 오류: {e}")
            self.status_var.set("계산 실패")
        finally:
            self.validator.set_busy(False)

    def _on_calculate_and_save(self) -> None:
        self._recalculate(save=True)
        if self._result is not None and not self._result.is_empty:
            messagebox.showinfo(
                "Success",
                f"보고서 및 Civil3D 출력 완료\n"
                f"IP: {len(self._result.curves)}개\n"
                f"출력 폴더: {Config.OUTPUT_DIR}",
            )

    # ------------------------------------------------------------------
    # 검증 결과 반영
    # ------------------------------------------------------------------
    def _apply_validation(self, result: AlignmentResult) -> None:
        issues = list(result.issues or [])
        self.validator.set_results([
            {
                "severity": it.severity.value,   # "ok" / "warn" / "error"
                "code": it.code,
                "message": it.message,
                "ip_no": it.ip_no,
            }
            for it in issues
        ])
        if issues:
            self.ip_table.apply_validation(group_issues_by_ip(issues))

    # ------------------------------------------------------------------
    # 미리보기
    # ------------------------------------------------------------------
    def _refresh_preview(self) -> None:
        if self._result is None or not self._result.curves:
            self.preview.clear()
            return
        ip_points = [tuple(c.ip_xy) for c in self._result.curves]
        element_points = (
            [tuple(p) for p in self._result.polycurve]
            if self._result.polycurve else None
        )
        self.preview.plot_alignment(
            ip_points=ip_points, element_points=element_points
        )

    # ------------------------------------------------------------------
    # IP 번호 ↔ 인덱스 매핑
    # ------------------------------------------------------------------
    def _ip_index_of(self, ip_no: int) -> int:
        """ip_no → result.curves 내 0-based 인덱스."""
        if self._result:
            for i, c in enumerate(self._result.curves):
                if c.ip_no == ip_no:
                    return i
        return max(0, ip_no - 1)

    def _raw_index_of(self, ip_no: int) -> Optional[int]:
        """ip_no → raw_lines 인덱스. raw_lines[0]=BP, raw_lines[1]=IP1."""
        if not self._raw_lines:
            return None
        idx = ip_no  # IP1 ↔ raw_lines[1]
        if 0 <= idx < len(self._raw_lines):
            return idx
        return None

    # ------------------------------------------------------------------
    # IP 테이블 콜백
    # ------------------------------------------------------------------
    def _on_ip_select(self, ip_no: int) -> None:
        self.preview.highlight_ip(self._ip_index_of(ip_no))

    def _on_ip_edit(self, ip_no: int, field: str, new_value: str) -> None:
        if field in ("x", "y", "r"):
            # 기존 raw_lines 갱신 경로
            if not self._raw_lines:
                return
            raw_idx = self._raw_index_of(ip_no)
            if raw_idx is None or raw_idx <= 0:
                return
            row = list(self._raw_lines[raw_idx])
            try:
                val = float(new_value)
            except ValueError:
                return
            col_map = {"y": 0, "x": 1, "r": 2}
            col = col_map.get(field)
            if col is None:
                return
            while len(row) <= col:
                row.append("0")
            row[col] = str(val)
            self._raw_lines[raw_idx] = row
            self._recalculate(save=False)
        elif field in ("m", "v", "z"):
            # raw_lines는 건드리지 않음. 테이블 값만 갱신 후 재계산
            self._recalculate(save=False)

    def _on_ip_insert(self, ip_no: int) -> None:
        if not self._raw_lines:
            messagebox.showwarning("안내", "먼저 파일을 열어주세요.")
            return
        raw_idx = self._raw_index_of(ip_no) or max(1, len(self._raw_lines) - 1)
        base = (
            list(self._raw_lines[raw_idx])
            if 0 < raw_idx < len(self._raw_lines)
            else ["0", "0", "0"]
        )
        self._raw_lines.insert(raw_idx, base)
        self.ip_table.load_raw(self._raw_lines)
        self._recalculate(save=False)

    def _on_ip_delete(self, ip_no: int) -> None:
        if not self._raw_lines:
            return
        raw_idx = self._raw_index_of(ip_no)
        if raw_idx is None or not (0 < raw_idx < len(self._raw_lines) - 1):
            messagebox.showwarning("삭제 불가", "BP/EP는 삭제할 수 없습니다.")
            return
        del self._raw_lines[raw_idx]
        self.ip_table.load_raw(self._raw_lines)
        self._recalculate(save=False)

    # ------------------------------------------------------------------
    # 미리보기 / 검증 콜백
    # ------------------------------------------------------------------
    def _on_preview_ip_click(self, ip_index: int) -> None:
        if self._result and 0 <= ip_index < len(self._result.curves):
            self.ip_table.select_ip_no(self._result.curves[ip_index].ip_no)

    def _on_issue_select(self, ip_no: Optional[int]) -> None:
        if ip_no is None:
            self.preview.highlight_ip(None)
            return
        self.ip_table.select_ip_no(ip_no)
        self.preview.highlight_ip(self._ip_index_of(ip_no))

    # ------------------------------------------------------------------
    # DXF / 조회
    # ------------------------------------------------------------------

    def _on_export_dxf(self) -> None:
        try:
            cfg = self.service.dxf_config

            # ✅ 도면 출력 시 unit은 프리셋의 sub_tick이 대체
            effective_unit = cfg.sub_tick

            base = Config.DXF_FILENAME.rsplit(".", 1)[0]
            filename = f"{base}.dxf"  # ✅ scale 태그 없음

            path = self.service.export_dxf(
                config=cfg,
                unit=effective_unit,
                filename=filename,
            )
            messagebox.showinfo("Success", f"도면 생성 완료:\n{path}")
        except NotImplementedError as e:
            messagebox.showwarning(
                "미구현 블록 타입",
                f"{e}\n\n도면 설정에서 '기본' 또는 '간략' 블록을 선택해 주세요.",
            )
        except AlignmentServiceError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            logger.exception("DXF 출력 오류")
            messagebox.showerror("Error", f"DXF 출력 실패: {e}")

    def _on_lookup_coord(self) -> None:
        try:
            sta = float(self.entry_station.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Input Error", "유효한 측점을 입력하세요.")
            return
        try:
            coord = self.service.get_coordinate(sta)
        except AlignmentServiceError as e:
            messagebox.showerror("Error", str(e))
            return
        if coord:
            messagebox.showinfo("Result", f"X = {coord[0]:.4f}, Y = {coord[1]:.4f}")
        else:
            messagebox.showerror("Error", "좌표를 찾을 수 없습니다.")

    def _on_lookup_station(self) -> None:
        try:
            x, y = map(float, self.entry_coord.get().split(","))
        except ValueError:
            messagebox.showerror("Input Error", "좌표를 'x,y' 형식으로 입력하세요.")
            return
        try:
            sta = self.service.get_station(x, y)
        except AlignmentServiceError as e:
            messagebox.showerror("Error", str(e))
            return
        if sta is not None:
            messagebox.showinfo("Result", f"측점: {format_station(sta)}")
        else:
            messagebox.showerror("Error", "측점을 찾을 수 없습니다.")

    def _on_auto_toggle(self, ip_no: int, auto: bool) -> None:
        self._recalculate(save=False)

    def _on_type_toggle(self, ip_no: int, curve_type: str) -> None:
        self._recalculate(save=False)

    def _on_open_dxf_settings(self) -> None:
        """도면 설정 다이얼로그 열기."""
        dialog = DXFSettingsDialog(
            self.root,
            config=self.service.dxf_config,
            on_apply=self._on_dxf_config_applied,
        )
        self.wait_window(dialog)

    def _on_dxf_config_applied(self, config: DXFConfig) -> None:
        """도면 설정 적용 콜백."""
        self.service.dxf_config = config
        self.status_var.set("도면 설정이 적용되었습니다.")

    AUTO_SAVE_INTERVAL_MS = 5 * 60 * 1000  # 5분

    def _schedule_auto_save(self):
        """자동 저장 스케줄러 (재귀)"""
        if self._auto_save_job is not None:
            self.root.after_cancel(self._auto_save_job)
        self._auto_save_job = self.root.after(
            self.AUTO_SAVE_INTERVAL_MS, self._auto_save_tick,
        )

    def _auto_save_tick(self):
        """5분마다 자동 저장. 프로젝트 파일이 있으면 덮어쓰기, 없으면 스킵."""
        try:
            from pathlib import Path
            if (self._current_project and self._raw_lines
                    and Path(self._current_project).exists()):
                self._save_project_to(self._current_project, silent=True)
        except Exception:
            logger.exception("자동 저장 실패")
        finally:
            self._schedule_auto_save()  # 재귀 스케줄

    def _on_close(self):
        """앱 종료 시 자동 저장 + 종료"""
        if self._auto_save_job is not None:
            self.root.after_cancel(self._auto_save_job)
            self._auto_save_job = None
        try:
            if self._current_project and self._raw_lines:
                self._save_project_to(self._current_project, silent=True)
        except Exception:
            logger.exception("종료 시 저장 실패")
        self.root.destroy()

    def _collect_project_state(self) -> ProjectData:
        """현재 GUI 상태 → ProjectData"""

        def _int(entry, default):
            try:
                return int(entry.get())
            except (ValueError, tk.TclError):
                return default

        def _float(entry, default):
            try:
                return float(entry.get())
            except (ValueError, tk.TclError):
                return default

        return ProjectData(
            raw_lines=self._raw_lines or [],
            source_file=self._current_file or "",
            unit=_int(self.entry_unit, Config.DEFAULT_UNIT),
            start_sta=_float(self.entry_start, Config.DEFAULT_START_STA),
            design_speed=_int(self.entry_speed, Config.DEFAULT_DESIGN_SPEED),
            ballast="자갈도상" if self.ballast_var.get() == 0 else "콘크리트도상",
            auto_flags=dict(self.ip_table._auto_flags),
            type_overrides=dict(self.ip_table._type_overrides),
            parameter_overrides=self.ip_table.get_parameter_overrides(),
            dxf_config=self.service.dxf_config.to_dict(),
        )

    def _apply_project_state(self, data: ProjectData) -> None:
        """ProjectData → GUI 복원 + 재계산"""
        # 1) 입력 데이터
        self._raw_lines = data.raw_lines
        self._current_file = data.source_file

        # 2) 계산 파라미터
        self._set_entry(self.entry_unit, str(data.unit))
        self._set_entry(self.entry_start, str(data.start_sta))
        self._set_entry(self.entry_speed, str(data.design_speed))
        self.ballast_var.set(0 if data.ballast == "자갈도상" else 1)

        # 3) 도면 설정
        try:
            from src.railway_alignment.io.dxf_config import DXFConfig
            self.service.dxf_config = DXFConfig.from_dict(data.dxf_config)
        except Exception:
            logger.exception("도면 설정 복원 실패 (기본값 유지)")

        # 4) IP 테이블 상태 (pending)
        self.ip_table.set_state({
            "auto_flags": data.auto_flags,
            "type_overrides": data.type_overrides,
        })

        # 5) raw 로드 + 재계산
        self.ip_table.load_raw(data.raw_lines)
        self._recalculate(save=False)

        # 6) M/V/Z 오버라이드 복원
        self._restore_parameter_overrides(data.parameter_overrides)
        self._recalculate(save=False)

    def _set_entry(self, entry, value):
        entry.delete(0, "end")
        entry.insert(0, value)

    def _restore_parameter_overrides(self, overrides: dict) -> None:
        """수동 M/V/Z 값을 IP 테이블에 반영"""
        for ip_no, params in (overrides or {}).items():
            iid = str(ip_no)
            if not self.ip_table.tree.exists(iid):
                continue
            self.ip_table._auto_flags[ip_no] = False
            self.ip_table.tree.set(iid, "auto", "")
            self.ip_table.tree.set(iid, "m", f"{params['m']:.1f}")
            self.ip_table.tree.set(iid, "v", f"{params['v']:.0f}")
            self.ip_table.tree.set(iid, "z", f"{params['z']:.4f}")
            self.ip_table._apply_row_style(ip_no)

    # ---------- 프로젝트 열기/저장 ----------
    def _on_open_project(self, path: Optional[str] = None):
        if path is None:
            path = filedialog.askopenfilename(
                title="프로젝트 열기", filetypes=PROJECT_FILETYPES,
            )
        if not path:
            return
        try:
            data = load_project(path)
        except ProjectIOError as e:
            messagebox.showerror("오류", str(e))
            return

        self._apply_project_state(data)
        from pathlib import Path
        self._current_project = str(Path(path).resolve())
        add_recent_project(self._current_project)
        self._refresh_recent_menu()
        self.status_var.set(f"프로젝트 로드: {Path(path).name}")

    def _on_save_project(self):
        if not self._raw_lines:
            messagebox.showwarning("안내", "먼저 데이터를 열어주세요.")
            return
        if not self._current_project:
            return self._on_save_project_as()
        self._save_project_to(self._current_project)

    def _on_save_project_as(self):
        if not self._raw_lines:
            messagebox.showwarning("안내", "먼저 데이터를 열어주세요.")
            return
        path = filedialog.asksaveasfilename(
            title="프로젝트 저장",
            defaultextension=PROJECT_EXTENSION,
            filetypes=PROJECT_FILETYPES,
        )
        if not path:
            return
        self._save_project_to(path)

    def _save_project_to(self, path: str, silent: bool = False):
        try:
            data = self._collect_project_state()
            saved = save_project(path, data)
            self._current_project = str(saved)
            add_recent_project(saved)
            self._refresh_recent_menu()
            if not silent:
                messagebox.showinfo("완료", f"프로젝트 저장:\n{saved}")
            from pathlib import Path
            self.status_var.set(f"프로젝트 저장: {Path(saved).name}")
        except ProjectIOError as e:
            if not silent:
                messagebox.showerror("오류", str(e))

    # ---------- 최근 파일 ----------
    def _refresh_recent_menu(self):
        if self._menu_recent is None:
            return
        self._menu_recent.delete(0, "end")
        recent = load_recent_projects()
        if not recent:
            self._menu_recent.add_command(label="(없음)", state="disabled")
            return
        for p in recent:
            from pathlib import Path
            self._menu_recent.add_command(
                label=Path(p).name,
                command=lambda pp=p: self._on_open_project(pp),
            )

    def _on_clear_recent(self):
        clear_recent_projects()
        self._refresh_recent_menu()