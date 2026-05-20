import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

from function import format_distance


class PlotCrossSection:
    def __init__(self, master):
        # 차트 영역
        self.master = master
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def draw_chart(self, data):
        """전달받은 2D 데이터를 Matplotlib에 그리기"""
        self.ax.clear()

        center = data['center']
        fh_z = center[2]  # 계획고(FH)
        gh_z = data.get('gl', fh_z)  # 안전장치 적용
        track_width = data['track_width']

        # 1. 지반선 플로팅
        dist_g, elev_g = data['ground']
        corrected_dist_g = -np.array(dist_g)
        self.ax.plot(corrected_dist_g, elev_g, color='green', label='Ground', lw=1.5)

        # 2. 동적 선로 폭 계산
        half_w = track_width / 2.0

        # 3. 사면 데이터 파싱
        ld = data['left_dist']
        rd = data['right_dist']

        # 사면 끝점 고도(Z) 추출
        _, elev_l = data['slope_l']
        _, elev_r = data['slope_r']

        # 4. 좌측 사면선 (선로 좌측 에지에서 사면 외곽 Catch Point까지)
        x_left = [-half_w - ld, -half_w]
        y_left = [elev_l, fh_z]
        self.ax.plot(x_left, y_left, color='purple', lw=2, label='Left Slope')

        # 5. 우측 사면선 (선로 우측 에지에서 사면 외곽 Catch Point까지)
        x_right = [half_w, half_w + rd]
        y_right = [fh_z, elev_r]
        self.ax.plot(x_right, y_right, color='red', lw=2, label='Right Slope')

        # 6. 선로 상면 노반선
        self.ax.plot([-half_w, half_w], [fh_z, fh_z], color='black', lw=3, label='Track Bed')

        # -------------------------------------------------------------
        # 🏷️ [신규 추가] 사면 기울기(1:n) 텍스트 마킹 로직
        # -------------------------------------------------------------
        # 메인 가동 중인 기울기 속성(slope_ratio)을 마스터에서 가져옴 (없으면 역산)
        slope_ratio = getattr(self.master, 'slope_ratio', 1.5)

        # 좌측 사면 중점 및 텍스트 배치 계산
        if ld > 0 and abs(fh_z - elev_l) > 0.01:
            mid_x_l = sum(x_left) / 2.0
            mid_y_l = sum(y_left) / 2.0
            # 수평 거리와 수직 고도차를 이용해 실제 기울기비(n) 검증 후 포맷팅
            n_l = ld / abs(fh_z - elev_l)
            # 사면선 살짝 위쪽으로 여백 배치
            self.ax.text(
                mid_x_l, mid_y_l + 1.0, f"1:{n_l:.1f}",
                color='purple', fontsize=10, weight='bold',
                horizontalalignment='center', verticalalignment='bottom'
            )

        # 우측 사면 중점 및 텍스트 배치 계산
        if rd > 0 and abs(fh_z - elev_r) > 0.01:
            mid_x_r = sum(x_right) / 2.0
            mid_y_r = sum(y_right) / 2.0
            n_r = rd / abs(fh_z - elev_r)
            self.ax.text(
                mid_x_r, mid_y_r + 1.0, f"1:{n_r:.1f}",
                color='red', fontsize=10, weight='bold',
                horizontalalignment='center', verticalalignment='bottom'
            )

        # 7. 레이아웃 및 뷰 설정
        self.ax.legend()
        self.ax.set_aspect('equal', adjustable='box')  # 1:1 정스케일 강제
        self.ax.set_ylim(fh_z - 30, fh_z + 30)  # 타겟 주변으로 뷰 좁혀서 가독성 확보

        try:
            station_text = format_distance(data['station'])
        except Exception:
            station_text = f"{data['station']}"

        self.ax.set_title(f"Station: {station_text}  FH: {fh_z:.2f}  GH: {gh_z:.2f}")
        self.canvas.draw()

        self.master.status_var.set("연산 완료")
        self.master.station_label.config(text=f"측점: {data['station']}")