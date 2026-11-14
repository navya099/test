import math
import tkinter as tk
from typing import List, Optional, Any

from profile.profile import Profile


# ==============================================================================
# 3. Civil 3D 스타일 종단뷰(Profile View) 실시간 Tkinter 시각화 앱
# ==============================================================================
class Civil3DProfileViewerApp:
    def __init__(self, root, layout_profile: Profile):
        self.root = root
        self.profile = layout_profile
        self.root.title(f"Civil 3D Profile View - [{self.profile.name}]")

        self.W, self.H = 1050, 620
        self.canvas = tk.Canvas(root, width=self.W, height=self.H, bg="#14171a")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 종단뷰 여백 및 데이터 밴드(하단 측점/계획고/지반고 표) 영역 설정
        self.margin_left = 85
        self.margin_right = 45
        self.margin_top = 45
        self.band_height = 95
        self.plot_bottom = self.H - self.band_height - 20
        self.plot_top = self.margin_top
        self.plot_left = self.margin_left
        self.plot_right = self.W - self.margin_right

        # 표고(EL) 범위 자동 설정
        self.min_sta = self.profile.start_station
        self.max_sta = self.profile.end_station
        all_els = [p.elevation for p in self.profile.pvi_list]
        self.min_el = math.floor((min(all_els) - 3.0) / 2.0) * 2.0
        self.max_el = math.ceil((max(all_els) + 3.0) / 2.0) * 2.0

        # 가상 현지지반선(Existing Ground, EG) 샘플 생성
        self.eg_points = self._generate_sample_eg()
        self._draw_profile_view_grid_and_bands()
        self._draw_profiles()

        # 마우스 추적 이벤트 바인딩 수정 완료
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def _generate_sample_eg(self):
        """비교용 현지지반선(EG) 생성 (계획선 대비 성토/절토 시각 확인용)"""
        pts = []
        steps = 80
        for i in range(steps + 1):
            sta = self.min_sta + (self.max_sta - self.min_sta) * (i / steps)
            fg_el, _ = self.profile.elevation_and_grade_at(sta)
            eg_el = fg_el - 1.2 * math.sin(sta * 0.012) + 0.8 * math.cos(sta * 0.025) - 0.5
            pts.append((sta, eg_el))
        return pts

    def sta_to_x(self, sta: float) -> float:
        ratio = (sta - self.min_sta) / (self.max_sta - self.min_sta)
        return self.plot_left + ratio * (self.plot_right - self.plot_left)

    def x_to_sta(self, x: float) -> float:
        ratio = (x - self.plot_left) / (self.plot_right - self.plot_left)
        return self.min_sta + ratio * (self.max_sta - self.min_sta)

    def el_to_y(self, el: float) -> float:
        ratio = (el - self.min_el) / (self.max_el - self.min_el)
        return self.plot_bottom - ratio * (self.plot_bottom - self.plot_top)

    @staticmethod
    def fmt_sta(sta: float) -> str:
        km = int(sta // 1000)
        m = sta % 1000
        return f"{km}+{m:06.2f}"

    def _draw_profile_view_grid_and_bands(self):
        """Civil 3D 스타일 종단 그리드 및 하단 데이터 밴드(Data Bands) 렌더링"""
        self.canvas.create_rectangle(
            self.plot_left, self.plot_top, self.plot_right, self.plot_bottom,
            outline="#4a5568", width=1.5
        )
        self.canvas.create_text(
            self.plot_left, 20, anchor="w", fill="#00d2ff", font=("맑은 고딕", 11, "bold"),
            text=f"PROFILE VIEW: {self.profile.name}  (Vertical Exaggeration: 10x)"
        )

        el_step = 2.0
        curr_el = self.min_el
        while curr_el <= self.max_el + 1e-6:
            y = self.el_to_y(curr_el)
            self.canvas.create_line(self.plot_left, y, self.plot_right, y, fill="#252a30", width=1)
            self.canvas.create_text(self.plot_left - 8, y, anchor="e", fill="#a0aec0", font=("Consolas", 9),
                                    text=f"{curr_el:.1f}m")
            curr_el += el_step

        band_top = self.plot_bottom + 8
        row_h = 28
        labels = ["측점 (STA)", "계획고 (FG)", "지반고 (EG)"]
        for idx, lbl in enumerate(labels):
            y1 = band_top + idx * row_h
            y2 = y1 + row_h
            self.canvas.create_rectangle(15, y1, self.plot_right, y2, outline="#4a5568", fill="#1b2026")
            self.canvas.create_line(self.plot_left, y1, self.plot_left, y2, fill="#4a5568")
            self.canvas.create_text(22, (y1 + y2) / 2, anchor="w", fill="#cbd5e0", font=("맑은 고딕", 8, "bold"), text=lbl)

        sta_step = 100.0
        curr_sta = math.ceil(self.min_sta / sta_step) * sta_step
        while curr_sta <= self.max_sta + 1e-6:
            x = self.sta_to_x(curr_sta)
            self.canvas.create_line(x, self.plot_top, x, self.plot_bottom, fill="#252a30", width=1)
            fg_el, _ = self.profile.elevation_and_grade_at(curr_sta)
            eg_el = min(self.eg_points, key=lambda p: abs(p[0] - curr_sta))[1]
            self.canvas.create_text(x, band_top + 14, text=self.fmt_sta(curr_sta), fill="#e2e8f0", font=("Consolas", 8))
            self.canvas.create_text(x, band_top + row_h + 14, text=f"{fg_el:.2f}", fill="#ff6b6b", font=("Consolas", 8))
            self.canvas.create_text(x, band_top + 2 * row_h + 14, text=f"{eg_el:.2f}", fill="#68d391",
                                    font=("Consolas", 8))
            curr_sta += sta_step

    def _draw_profiles(self):
        """현지지반선(EG), 계획선(FG), 접선 보조선, PVI/BVC/EVC 마커 렌더링"""
        eg_coords = []
        for sta, el in self.eg_points:
            eg_coords.extend([self.sta_to_x(sta), self.el_to_y(el)])
        self.canvas.create_line(*eg_coords, fill="#48bb78", width=1.5, dash=(4, 2))

        pvi_coords = []
        for pvi in self.profile.pvi_list:
            px, py = self.sta_to_x(pvi.station), self.el_to_y(pvi.elevation)
            pvi_coords.extend([px, py])
            self.canvas.create_polygon(px, py, px - 6, py - 10, px + 6, py - 10, outline="#ecc94b", fill="", width=1.5)
            self.canvas.create_text(px, py - 16, text=f"{pvi.name}\nEL {pvi.elevation:.2f}", fill="#ecc94b",
                                    font=("Consolas", 8))
        self.canvas.create_line(*pvi_coords, fill="#718096", width=1, dash=(2, 2))

        fg_coords = []
        samples = 250
        for i in range(samples + 1):
            sta = self.min_sta + (self.max_sta - self.min_sta) * (i / samples)
            el, _ = self.profile.elevation_and_grade_at(sta)
            fg_coords.extend([self.sta_to_x(sta), self.el_to_y(el)])
        self.canvas.create_line(*fg_coords, fill="#ff4d4d", width=2.5)

        for r in self.profile.pvi_report:
            if r["total_L"] > 0:
                for label, s_val, e_val in [("BVC", r["bvc_sta"], r["bvc_el"]), ("EVC", r["evc_sta"], r["evc_el"])]:
                    bx, by = self.sta_to_x(s_val), self.el_to_y(e_val)
                    self.canvas.create_oval(bx - 3, by - 3, bx + 3, by + 3, fill="#00d2ff", outline="")
                if r["extrema_sta"] is not None:
                    hx, hy = self.sta_to_x(r["extrema_sta"]), self.el_to_y(r["extrema_el"])
                    self.canvas.create_oval(hx - 4, hy - 4, hx + 4, hy + 4, fill="#f6e05e", outline="#1a202c")
                    self.canvas.create_text(hx, hy + 14, text=f"극점\n{self.fmt_sta(r['extrema_sta'])}", fill="#f6e05e",
                                            font=("Consolas", 8))

    def on_mouse_move(self, event):
        """Civil 3D 종단뷰 실시간 십자선 및 계획고/경사/절성토 툴팁"""
        self.canvas.delete("profile_tracker")
        mx, my = event.x, event.y
        if not (self.plot_left <= mx <= self.plot_right and self.plot_top <= my <= self.plot_bottom):
            return
        sta = self.x_to_sta(mx)
        fg_el, grade = self.profile.elevation_and_grade_at(sta)
        eg_el = min(self.eg_points, key=lambda p: abs(p[0] - sta))[1]
        diff_el = fg_el - eg_el
        fy = self.el_to_y(fg_el)

        self.canvas.create_line(mx, self.plot_top, mx, self.plot_bottom, fill="#00d2ff", dash=(3, 3),
                                tags="profile_tracker")
        self.canvas.create_oval(mx - 4, fy - 4, mx + 4, fy + 4, fill="#ff4d4d", outline="#ffffff", width=1.5,
                                tags="profile_tracker")

        cut_fill = f"성토 +{diff_el:.2f}m" if diff_el >= 0 else f"절토 {diff_el:.2f}m"
        tooltip = (
            f"STA   : {self.fmt_sta(sta)}\n"
            f"계획고: {fg_el:.3f} m\n"
            f"경사  : {grade * 100:+.3f} %\n"
            f"지반차: {cut_fill}"
        )
        tx = mx + 15 if mx < self.plot_right - 165 else mx - 165
        ty = fy - 45 if fy > self.plot_top + 60 else fy + 15
        t_id = self.canvas.create_text(tx + 8, ty + 6, anchor="nw", text=tooltip, fill="#ffffff",
                                       font=("Consolas", 9, "bold"), tags="profile_tracker")
        bbox = self.canvas.bbox(t_id)
        if bbox:
            r_id = self.canvas.create_rectangle(bbox[0] - 6, bbox[1] - 4, bbox[2] + 6, bbox[3] + 4, fill="#1a202c",
                                                outline="#00d2ff", tags="profile_tracker")
            self.canvas.tag_raise(t_id, r_id)