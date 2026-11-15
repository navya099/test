# ==============================================================================
# 2. Civil 3D 3D 드라이브(Drive) 가상 주행 시뮬레이터 GUI
# ==============================================================================
import tkinter as tk
import math

from model3d.road3d import RoadModel3D


class Civil3DDriveSimulator:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Civil 3D 3D Drive (가상 주행 시뮬레이션)")
        self.root.geometry("1280x780")
        self.root.configure(bg="#0f172a")
        self.road = RoadModel3D()
        self.curr_sta = 0.0
        self.is_playing = True
        self.speed_kmh = 80.0       # 주행 속도 (km/h)
        self.lane_offset = 1.75     # 운전자 위치 (우측 주행차로 중심 +1.75m)
        self.eye_height = 1.25      # 운전자 눈높이 (m)
        self.dt = 0.033             # 프레임 간격 (약 30 FPS)
        self._build_ui()
        self._animate_loop()

    def _build_ui(self):
        # 3D 주행 메인 캔버스
        self.canvas = tk.Canvas(self.root, bg="#0b1120", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 하단 드라이브 컨트롤 패널 (Civil 3D Drive 리본/플레이어 스타일)
        ctrl = tk.Frame(self.root, bg="#1e293b", height=64, padx=14, pady=8)
        ctrl.pack(fill=tk.X, side=tk.BOTTOM)

        btn_cfg = {"font": ("맑은 고딕", 9, "bold"), "bd": 0, "padx": 12, "pady": 6, "cursor": "hand2"}
        self.btn_play = tk.Button(ctrl, text="⏸ 일시정지", bg="#0284c7", fg="white", command=self.toggle_play, **btn_cfg)
        self.btn_play.pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(ctrl, text="⏮ 처음으로", bg="#334155", fg="white", command=self.reset_drive, **btn_cfg).pack(side=tk.LEFT, padx=4)

        # 주행 속도 조절 슬라이더
        tk.Label(ctrl, text="속도(km/h):", bg="#1e293b", fg="#cbd5e0", font=("맑은 고딕", 9, "bold")).pack(side=tk.LEFT, padx=(16, 4))
        self.speed_var = tk.DoubleVar(value=self.speed_kmh)
        tk.Scale(
            ctrl, from_=20, to=140, orient=tk.HORIZONTAL, variable=self.speed_var,
            bg="#1e293b", fg="#38bdf8", troughcolor="#0f172a", highlightthickness=0, length=140,
            command=lambda v: setattr(self, "speed_kmh", float(v))
        ).pack(side=tk.LEFT)

        # 차선 위치 선택 (우측 주행차로 / 중앙선 / 좌측 차로)
        tk.Label(ctrl, text="주행 차로:", bg="#1e293b", fg="#cbd5e0", font=("맑은 고딕", 9, "bold")).pack(side=tk.LEFT, padx=(16, 4))
        for label, off_val in [("좌측(-1.75m)", -1.75), ("중심(0m)", 0.0), ("우측(+1.75m)", 1.75)]:
            tk.Button(
                ctrl, text=label, bg="#334155", fg="#e2e8f0", font=("맑은 고딕", 8), bd=0, padx=8, pady=4,
                command=lambda o=off_val: setattr(self, "lane_offset", o)
            ).pack(side=tk.LEFT, padx=2)

        # 측점 탐색 타임라인 슬라이더
        tk.Label(ctrl, text="측점 이동:", bg="#1e293b", fg="#cbd5e0", font=("맑은 고딕", 9, "bold")).pack(side=tk.LEFT, padx=(16, 4))
        self.sta_slider = tk.Scale(
            ctrl, from_=0.0, to=self.road.total_length - 30.0, orient=tk.HORIZONTAL,
            bg="#1e293b", fg="#facc15", troughcolor="#0f172a", highlightthickness=0, length=240,
            showvalue=False, command=self.on_slider_drag
        )
        self.sta_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.btn_play.config(
            text="⏸ 일시정지" if self.is_playing else "▶ 주행 시작",
            bg="#0284c7" if self.is_playing else "#059669"
        )

    def reset_drive(self):
        self.curr_sta = 0.0
        self.sta_slider.set(0.0)
        self.render_3d_frame()

    def on_slider_drag(self, val):
        self.curr_sta = float(val)
        if not self.is_playing:
            self.render_3d_frame()

    @staticmethod
    def fmt_sta(sta: float) -> str:
        return f"{int(sta // 1000)}+{sta % 1000:06.2f}"

    def _animate_loop(self):
        if self.is_playing:
            # 시속(km/h) -> 초당 이동거리(m/s) 변환 후 프레임 시간(dt)만큼 전진
            v_ms = (self.speed_kmh * 1000.0) / 3600.0
            self.curr_sta += v_ms * self.dt
            if self.curr_sta >= self.road.total_length - 30.0:
                self.curr_sta = 0.0
            self.sta_slider.set(self.curr_sta)
            self.render_3d_frame()
        self.root.after(int(self.dt * 1000), self._animate_loop)

    def render_3d_frame(self):
        c = self.canvas
        c.delete("all")
        w, h = max(200, c.winfo_width()), max(200, c.winfo_height())

        # 1. 하늘 및 원경 지평선 배경 그리기
        horizon_y = h * 0.44
        c.create_rectangle(0, 0, w, horizon_y, fill="#0c192c", outline="")
        c.create_rectangle(0, horizon_y, w, h, fill="#111827", outline="")

        # 2. 카메라 위치(Eye) 및 전방 주시 벡터(Forward, Right, Up) 계산
        cam_sta = self.curr_sta
        look_sta = min(self.road.total_length, cam_sta + 22.0)

        cam_e, cam_n = self.road.point_xy(cam_sta, self.lane_offset)
        cam_cl_z, curr_grade = self.road.elevation_grade(cam_sta)
        l_slp, r_slp, _, _ = self.road.get_slopes_and_widths(cam_sta)
        curr_cross_slope = r_slp if self.lane_offset >= 0 else l_slp
        cam_z = cam_cl_z + abs(self.lane_offset) * curr_cross_slope + self.eye_height

        tgt_e, tgt_n = self.road.point_xy(look_sta, self.lane_offset)
        tgt_cl_z, _ = self.road.elevation_grade(look_sta)
        tgt_z = tgt_cl_z + abs(self.lane_offset) * curr_cross_slope + self.eye_height * 0.85

        # 전방 단위 벡터 F
        fx, fy, fz = tgt_e - cam_e, tgt_n - cam_n, tgt_z - cam_z
        f_len = max(1e-6, math.hypot(fx, fy, fz))
        fx, fy, fz = fx / f_len, fy / f_len, fz / f_len

        # 세계 상방 벡터 (0, 0, 1)과 외적하여 우측 단위 벡터 R 산출
        rx, ry, rz = fy * 1.0 - fz * 0.0, fz * 0.0 - fx * 1.0, fx * 0.0 - fy * 0.0
        r_len = max(1e-6, math.hypot(rx, ry, rz))
        rx, ry, rz = rx / r_len, ry / r_len, rz / r_len

        # 카메라 상방 벡터 U = R x F
        ux, uy, uz = ry * fz - rz * fy, rz * fx - rx * fz, rx * fy - ry * fx

        # 편경사(Roll)에 따른 화면 미세 기울기 반영
        roll_ang = -curr_cross_slope * 0.65
        cos_r, sin_r = math.cos(roll_ang), math.sin(roll_ang)
        rx_r, ry_r, rz_r = rx * cos_r + ux * sin_r, ry * cos_r + uy * sin_r, rz * cos_r + uz * sin_r
        ux_r, uy_r, uz_r = -rx * sin_r + ux * cos_r, -ry * sin_r + uy * cos_r, -rz * sin_r + uz * cos_r

        fov_scale = w * 0.72  # 시야각(FOV 약 70도) 초점거리

        def project_3d(pt_3d):
            px, py, pz = pt_3d

            dx = px - cam_e
            dy = py - cam_n
            dz = pz - cam_z
            z_cam = dx * fx + dy * fy + dz * fz
            if z_cam <= 1.2:  # 카메라 뒤쪽이나 너무 가까운 점 클리핑
                return None
            x_cam = dx * rx_r + dy * ry_r + dz * rz_r
            y_cam = dx * ux_r + dy * uy_r + dz * uz_r
            sx = w * 0.5 + fov_scale * (x_cam / z_cam)
            sy = h * 0.48 - fov_scale * (y_cam / z_cam)
            return sx, sy

        # 3. 전방 600m 구간을 4m 간격 슬라이스로 샘플링 (Painter's Algorithm: 먼 곳부터 가까운 곳 역순 렌더링)
        view_dist = 600.0
        step = 4.0
        slices = []
        s_val = cam_sta + 2.0
        max_s = min(self.road.total_length, cam_sta + view_dist)
        while s_val <= max_s:
            slices.append(self.road.cross_section_3d(s_val))
            s_val += step

        # 먼 슬라이스부터 가까운 슬라이스 순으로 면(Polygon) 및 차선 그리기
        for i in range(len(slices) - 2, -1, -1):
            s_near = slices[i]
            s_far = slices[i + 1]
            dist_ratio = (i * step) / view_dist  # 0(가까움) ~ 1(멀음, 안개 효과)

            # 투영 좌표 계산
            keys = ["L_DAY", "L_EPS", "L_ETW", "CL", "R_ETW", "R_EPS", "R_DAY"]
            p_n = {k: project_3d(s_near[k]) for k in keys}
            p_f = {k: project_3d(s_far[k]) for k in keys}
            if any(p_n[k] is None or p_f[k] is None for k in keys):
                continue

            # 거리감(체커보드 음영) 표현을 위한 교차 명암
            shade = 1.0 - dist_ratio * 0.55
            is_even = (int((cam_sta + i * step) // step) % 2 == 0)

            # (1) 좌/우 비탈면(Daylight Slope - 녹색 계열)
            slope_col = f"#{int(22 * shade):02x}{int((75 if is_even else 62) * shade):02x}{int(45 * shade):02x}"
            for side_a, side_b in [("L_DAY", "L_EPS"), ("R_EPS", "R_DAY")]:
                c.create_polygon(*p_n[side_a], *p_n[side_b], *p_f[side_b], *p_f[side_a], fill=slope_col, outline="")

            # (2) 좌/우 길어깨(Shoulder - 짙은 회색)
            shd_col = f"#{int(45 * shade):02x}{int(52 * shade):02x}{int(62 * shade):02x}"
            for side_a, side_b in [("L_EPS", "L_ETW"), ("R_ETW", "R_EPS")]:
                c.create_polygon(*p_n[side_a], *p_n[side_b], *p_f[side_b], *p_f[side_a], fill=shd_col, outline="")

            # (3) 아스팔트 본선 차도면 (L_ETW ~ R_ETW)
            road_base = 58 if is_even else 50
            road_col = f"#{int(road_base * shade):02x}{int((road_base + 4) * shade):02x}{int((road_base + 10) * shade):02x}"
            c.create_polygon(*p_n["L_ETW"], *p_n["R_ETW"], *p_f["R_ETW"], *p_f["L_ETW"], fill=road_col, outline="")

            # (4) 차선 도색선 (중앙선 노란색 실선, 차선 외측 흰색 실선)
            c.create_line(*p_n["CL"], *p_f["CL"], fill="#facc15", width=max(1, int(3 * (1 - dist_ratio))))
            c.create_line(*p_n["L_ETW"], *p_f["L_ETW"], fill="#f8fafc", width=max(1, int(2 * (1 - dist_ratio))))
            c.create_line(*p_n["R_ETW"], *p_f["R_ETW"], fill="#f8fafc", width=max(1, int(2 * (1 - dist_ratio))))

        # 4. Civil 3D 스타일 1인칭 운전석 HUD (Head-Up Display) 오버레이
        self._draw_hud(w, h, cam_sta, cam_cl_z, curr_grade, l_slp, r_slp)

    def _draw_hud(self, w, h, sta, el, grade, l_slp, r_slp):
        c = self.canvas
        _, _, _, r_w = self.road.get_slopes_and_widths(sta)

        # 좌측 상단: 선형 기하 정보 HUD 박스
        c.create_rectangle(16, 16, 335, 138, fill="#0f172a", outline="#38bdf8", width=1.5)
        hud_text = (
            f"CIVIL 3D DRIVE TELEMETRY\n"
            f"──────────────────────────────\n"
            f"측점 (STA)   : {self.fmt_sta(sta)}\n"
            f"계획고 (EL)  : {el:.3f} m  (경사 {grade * 100:+.2f}%)\n"
            f"편경사 (L/R) : {l_slp * 100:+.2f}% / {r_slp * 100:+.2f}%\n"
            f"우측 차선폭  : {r_w:.2f} m {'[확폭구간]' if r_w > 3.55 else ''}"
        )
        c.create_text(28, 26, anchor="nw", text=hud_text, fill="#f8fafc", font=("Consolas", 9, "bold"))
        # 우측 상단: 디지털 속도계 & 편경사 롤 인디케이터
        c.create_rectangle(w - 190, 16, w - 16, 110, fill="#0f172a", outline="#facc15", width=1.5)
        c.create_text(w - 103, 32, text="SPEED", fill="#94a3b8", font=("Consolas", 8, "bold"))
        c.create_text(w - 103, 62, text=f"{int(self.speed_kmh)}", fill="#facc15", font=("Consolas", 24, "bold"))
        c.create_text(w - 103, 92, text="km/h", fill="#cbd5e0", font=("Consolas", 9))
        # 중앙 조준 십자선
        cx, cy = w * 0.5, h * 0.48
        c.create_line(cx - 12, cy, cx + 12, cy, fill="#38bdf8", width=1)
        c.create_line(cx, cy - 12, cx, cy + 12, fill="#38bdf8", width=1)

if __name__ == "__main__":
    root = tk.Tk()
    app = Civil3DDriveSimulator(root)
    root.mainloop()