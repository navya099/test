import tkinter as tk

from src.railway_alignment.core.constant_config import Config
from src.railway_alignment.core.math_util import format_station
from src.railway_alignment.io.parsers import read_alignment_file
from src.railway_alignment.service.alignment_service import AlignmentService, AlignmentInput, AlignmentServiceError

import logging

logger = logging.getLogger(__name__)

# ============================================================
# GUI
# ============================================================
class AlignmentApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Railway Alignment Tool v10")
        self.service = AlignmentService()
        self.last_unit = Config.DEFAULT_UNIT  # DXF 출력 시 재사용
        self._build_ui()

    def _build_ui(self):
        r = self.root

        tk.Label(r, text="계산 간격 (기본 20)").grid(row=0, column=0)
        self.entry_unit = tk.Entry(r)
        self.entry_unit.grid(row=0, column=1)

        tk.Label(r, text="시작 측점 (기본 0)").grid(row=1, column=0)
        self.entry_start = tk.Entry(r)
        self.entry_start.grid(row=1, column=1)

        tk.Label(r, text="설계 최고 속도 (기본 250)").grid(row=2, column=0)
        self.entry_speed = tk.Entry(r)
        self.entry_speed.grid(row=2, column=1)

        tk.Label(r, text="도상 유형").grid(row=3, column=0)
        self.ballast_var = tk.IntVar(value=0)
        tk.Radiobutton(r, text="자갈도상", variable=self.ballast_var, value=0).grid(row=3, column=1)
        tk.Radiobutton(r, text="콘크리트도상", variable=self.ballast_var, value=1).grid(row=3, column=2)

        tk.Button(r, text="계산 시작", command=self.run_calculation).grid(row=4, columnspan=3, pady=10)

        tk.Label(r, text="도면 축척").grid(row=5, column=0)
        self.entry_scale = tk.Entry(r)
        self.entry_scale.insert(0, "1000")
        self.entry_scale.grid(row=5, column=1)
        tk.Button(r, text="도면 출력", command=self.export_dxf).grid(row=5, column=2)

        tk.Label(r, text="측점 → 좌표").grid(row=6, column=0)
        self.entry_station = tk.Entry(r)
        self.entry_station.grid(row=6, column=1)
        tk.Button(r, text="좌표 계산", command=self.lookup_coord).grid(row=6, column=2)

        tk.Label(r, text="좌표 → 측점").grid(row=7, column=0)
        self.entry_coord = tk.Entry(r)
        self.entry_coord.grid(row=7, column=1)
        tk.Button(r, text="측점 찾기", command=self.lookup_station).grid(row=7, column=2)

        tk.Button(r, text="프로그램 종료", command=self.root.destroy).grid(row=8, columnspan=3, pady=10)

    def _read_inputs(self) -> tuple[int, float, int, str]:
        unit = int(self.entry_unit.get()) if self.entry_unit.get() else Config.DEFAULT_UNIT
        start_sta = float(self.entry_start.get()) if self.entry_start.get() else Config.DEFAULT_START_STA
        speed = int(self.entry_speed.get()) if self.entry_speed.get() else Config.DEFAULT_DESIGN_SPEED
        ballast = "자갈도상" if self.ballast_var.get() == 0 else "콘크리트도상"
        return unit, start_sta, speed, ballast

    # --------------------------------------------------------
    # 계산 시작 (서비스 위임)
    # --------------------------------------------------------
    def run_calculation(self):
        from tkinter import messagebox

        try:
            unit, start_sta, speed, ballast = self._read_inputs()
            self.last_unit = unit

            lines = read_alignment_file()
            if not lines:
                messagebox.showerror("Error", "선형 데이터를 읽을 수 없습니다.")
                return

            input_data = AlignmentInput(
                raw_lines=lines,
                unit=unit,
                start_sta=start_sta,
                design_speed=speed,
                ballast=ballast,
            )
            result = self.service.calculate(input_data)

            messagebox.showinfo(
                "Success",
                f"보고서 및 Civil3D 출력 완료\n"
                f"IP: {len(result.curves)}개\n"
                f"출력 폴더: {Config.OUTPUT_DIR}",
            )
        except AlignmentServiceError as e:
            logger.error("계산 실패: %s", e)
            messagebox.showerror("Error", str(e))
        except Exception as e:
            logger.exception("예상치 못한 오류")
            messagebox.showerror("Error", f"예상치 못한 오류: {e}")

    # --------------------------------------------------------
    # DXF 출력 (서비스 위임)
    # --------------------------------------------------------
    def export_dxf(self):
        from tkinter import messagebox

        try:
            scale = int(self.entry_scale.get()) if self.entry_scale.get() else Config.DEFAULT_SCALE
            if scale < Config.DEFAULT_SCALE:
                raise AlignmentServiceError("축척은 1000 이상이어야 합니다.")

            path = self.service.export_dxf(scale=scale)
            messagebox.showinfo("Success", f"도면 생성 완료:\n{path}")
        except AlignmentServiceError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            logger.exception("DXF 출력 오류")
            messagebox.showerror("Error", f"DXF 출력 실패: {e}")

    # --------------------------------------------------------
    # 조회
    # --------------------------------------------------------
    def lookup_coord(self):
        from tkinter import messagebox

        try:
            sta = float(self.entry_station.get())
            coord = self.service.get_coordinate(sta)
            if coord:
                messagebox.showinfo("Result", f"X = {coord[0]:.4f}, Y = {coord[1]:.4f}")
            else:
                messagebox.showerror("Error", "좌표를 찾을 수 없습니다.")
        except ValueError:
            messagebox.showerror("Input Error", "유효한 측점을 입력하세요.")
        except AlignmentServiceError as e:
            messagebox.showerror("Error", str(e))

    def lookup_station(self):
        from tkinter import messagebox

        try:
            x, y = map(float, self.entry_coord.get().split(","))
            sta = self.service.get_station(x, y)
            if sta is not None:
                messagebox.showinfo("Result", f"측점: {format_station(sta)}")
            else:
                messagebox.showerror("Error", "측점을 찾을 수 없습니다.")
        except ValueError:
            messagebox.showerror("Input Error", "좌표를 'x,y' 형식으로 입력하세요.")
        except AlignmentServiceError as e:
            messagebox.showerror("Error", str(e))