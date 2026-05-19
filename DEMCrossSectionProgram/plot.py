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
        gh_z = data['gl']
        track_width = data['track_width']
        # 1. 지반선 플로팅 (기존 유지)
        dist_g, elev_g = data['ground']
        corrected_dist_g = -np.array(dist_g)
        self.ax.plot(corrected_dist_g, elev_g, color='green', label='Ground', lw=1.5)

        # 2. 동적 선로 폭 계산 (하드코딩 제거)
        # SectionProvider에서 리턴해준 left, right 좌표의 상대 변위를 계산하거나
        # 클래스 속성의 track_width를 활용합니다.
        # 여기서는 data['left']가 3D 절대좌표이므로, 중심선(0) 기준 상대좌표인 half_w를 정의합니다.
        half_w = track_width / 2.0  # 만약 클래스 내부라면 self.track_width 사용

        # 3. 사면 데이터 파싱
        ld = data['left_dist']
        rd = data['right_dist']

        # 사면 끝점 고도(Z) 추출
        _, elev_l = data['slope_l']
        _, elev_r = data['slope_r']

        # 4. 좌측 사면선 (선로 좌측 에지에서 사면 외곽 Catch Point까지)
        # X축: [-half_w - ld] 에서 [-half_w] 까지
        # Y축: [elev_l] 에서 [fh_z] 까지
        self.ax.plot([-half_w - ld, -half_w], [elev_l, fh_z], color='purple', lw=2, label='Left Slope')

        # 5. 우측 사면선 (선로 우측 에지에서 사면 외곽 Catch Point까지)
        # X축: [half_w] 에서 [half_w + rd] 까지
        # Y축: [fh_z] 에서 [elev_r] 까지 (elev_l 오타 수정)
        self.ax.plot([half_w, half_w + rd], [fh_z, elev_r], color='red', lw=2, label='Right Slope')

        # 6. [옵션] 선로 상면 노반선 (도면의 완성도를 위해 좌측 에지와 우측 에지를 연결)
        self.ax.plot([-half_w, half_w], [fh_z, fh_z], color='black', lw=3, label='Track Bed')

        # 7. 레이아웃 및 뷰 설정
        self.ax.legend()
        self.ax.set_aspect('equal', adjustable='box')  # 1:1 정스케일 강제 (클레임 방지 필수)
        self.ax.set_ylim(fh_z - 30, fh_z + 30)  # 타겟 주변으로 뷰 좁혀서 가독성 확보
        self.ax.set_title(f"Station: {format_distance(data['station'])} FH: {fh_z:.2f} GH: {gh_z:.2f}")
        self.canvas.draw()

        self.master.status_var.set("연산 완료")
        self.master.station_label.config(text=f"측점: {data['station']}")