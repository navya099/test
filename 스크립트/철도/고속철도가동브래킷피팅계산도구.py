import math

import ezdxf
import matplotlib.pyplot as plt
from PIL import Image, ImageTk   # Pillow 라이브러리 필요

import tkinter as tk
from tkinter import messagebox

from math_utils import calculate_distance
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def export_dxf(data):
    # DXF 문서 생성
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    #데이터 언팩
    l, cw_point, mw_point, rl_to_slopepipoe_height, mast_height , slope_start,slope_end , top_start, top_end, registerarm_start_point, registerarm_end_point, rigid_suspenssion_start,rigid_suspenssion_end , aux_strut_tube_start, aux_strut_tube_end= data
    slope_start_x, slope_start_y = slope_start
    slope_end_x, slope_end_y = slope_end
    top_start_x, top_start_y = top_start
    top_end_x, top_end_y = top_end

    # 전주
    msp.add_line((-l, rl_to_slopepipoe_height), (-l, mast_height))
    # 경사파이프
    msp.add_line((slope_start_x, slope_start_y), (slope_end_x, slope_end_y))
    # 상부파이프
    msp.add_line((top_start_x, top_start_y), (top_end_x, top_end_y))
    #수평파이프
    msp.add_line((registerarm_start_point[0], registerarm_start_point[1]), (registerarm_end_point[0], registerarm_end_point[1]))

    #보조파이프
    msp.add_line((rigid_suspenssion_start[0], rigid_suspenssion_start[1]),
                 (rigid_suspenssion_end[0], rigid_suspenssion_end[1]))

    # 사각파이프
    msp.add_line((aux_strut_tube_start[0], aux_strut_tube_start[1]),
                 (aux_strut_tube_end[0], aux_strut_tube_end[1]))
    # 전차선, 조가선 포인트
    msp.add_circle(cw_point, radius=50)  # 전차선 표시
    msp.add_circle(mw_point, radius=50)  # 조가선 표시

    # DXF 저장
    doc.saveas("c:/temp/structure.dxf")

def plot(data, result):
    # 시각화
    # 데이터 언팩
    l, cw_point, mw_point, rl_to_slopepipoe_height, mast_height, slope_start, slope_end, top_start, top_end, registerarm_start_point, registerarm_end_point, rigid_suspenssion_start, rigid_suspenssion_end, aux_strut_tube_start, aux_strut_tube_end = data
    slope_start_x, slope_start_y = slope_start
    slope_end_x, slope_end_y = slope_end
    top_start_x, top_start_y = top_start
    top_end_x, top_end_y = top_end

    fig, ax = plt.subplots()
    ax.set_aspect('equal')

    # 전주
    ax.plot([-l, -l], [rl_to_slopepipoe_height, mast_height], 'g-', linewidth=2, label='전주')
    # 경사파이프
    ax.plot([slope_start_x, slope_end_x], [slope_start_y, slope_end_y], 'b-', linewidth=2, label='경사파이프')

    # 상부파이프 (경사파이프 끝점에서 상부로 연결)
    ax.plot([top_start_x, top_end_x], [top_start_y, top_end_y], 'r-', linewidth=2, label='상부파이프')

    #수평파이프
    ax.plot([registerarm_start_point[0], registerarm_end_point[0]], [registerarm_start_point[1], registerarm_end_point[1]], 'r-', linewidth=2, label='수평파이프')

    #보조파이프
    ax.plot([rigid_suspenssion_start[0], rigid_suspenssion_end[0]],
            [rigid_suspenssion_start[1], rigid_suspenssion_end[1]], 'r-', linewidth=2, label='보조파이프')

    # 사각파이프
    ax.plot([aux_strut_tube_start[0], aux_strut_tube_end[0]],
            [aux_strut_tube_start[1], aux_strut_tube_end[1]], 'r-', linewidth=2, label='사각파이프')
    # 조가선
    ax.scatter(mw_point[0], mw_point[1], color='b')
    # 전차선
    ax.scatter(cw_point[0], cw_point[1], color='r')

    # 설정
    plt.title('경사파이프 & 상부파이프 시각화')
    plt.xlabel('X (mm)')
    plt.ylabel('Y (mm)')
    plt.grid(True)
    plt.legend()
    plt.show()

def cal_aux_struct_tube(slope_start, slope_end, top_start, top_end, theta):
    # 경사파이프 중간점
    slope_start_x , slope_start_y = slope_start
    slope_end_x, slope_end_y = slope_end
    top_start_x, top_start_y = top_start
    top_end_x, top_end_y = top_end

    xm = (slope_start_x + slope_end_x) / 2
    ym = (slope_start_y + slope_end_y) / 2
    a1, b1 = math.cos(theta + math.pi / 2), math.sin(theta + math.pi / 2)

    # 상부파이프 벡터
    vx_top = top_end_x - top_start_x
    vy_top = top_end_y - top_start_y

    # 법선 벡터 정규화
    nx, ny = -vy_top, vx_top
    norm = math.sqrt(nx ** 2 + ny ** 2)
    nx, ny = nx / norm, ny / norm

    # OFFSET(-50) 적용
    offset = -50
    xt0_off = top_start_x + offset * nx
    yt0_off = top_start_y + offset * ny
    xt1_off = top_end_x + offset * nx
    yt1_off = top_end_y + offset * ny

    # 교차점 계산
    den = a1 * vy_top - b1 * vx_top
    num_t = (xt0_off - xm) * vy_top - (yt0_off - ym) * vx_top
    t = num_t / den
    TSx = xm + t * a1
    TSy = ym + t * b1

    #auxtube 시작점 tsx,tsy
    #끝점
    tex = xm + 50 * math.cos(theta + math.pi / 2)
    tey = ym + 50 * math.sin(theta + math.pi / 2)
    return [TSx, TSy], [tex, tey]

class MAINAPP(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("고속철도 브래킷 피팅 계산 도구")

        # 좌측 입력 프레임
        self.frame_left = tk.Frame(self)
        self.frame_left.grid(row=0, column=0, padx=10, pady=10)

        # 우측 이미지 프레임
        self.frame_right = tk.Frame(self)
        self.frame_right.grid(row=0, column=1, padx=10, pady=10)


        # 입력창
        tk.Label( self.frame_left, text="건식게이지").grid(row=0, column=0)
        self.entry_l = tk.Entry(self.frame_left)
        self.entry_l.insert(0, "2880")
        self.entry_l.grid(row=0, column=1)

        tk.Label( self.frame_left, text="편위").grid(row=1, column=0)
        self.entry_stagger = tk.Entry(self.frame_left)
        self.entry_stagger.insert(0, "-230")
        self.entry_stagger.grid(row=1, column=1)

        tk.Label( self.frame_left, text="가고").grid(row=2, column=0)
        self.entry_e = tk.Entry(self.frame_left)
        self.entry_e.insert(0, "1400")
        self.entry_e.grid(row=2, column=1)

        tk.Label(self.frame_left, text="하부브래킷 고정금구와 브래킷 피팅 높이차").grid(row=3, column=0)
        self.entry_f = tk.Entry(self.frame_left)
        self.entry_f.insert(0, "110")
        self.entry_f.grid(row=3, column=1)

        tk.Label(self.frame_left, text="상부,경사파이프 간격").grid(row=4, column=0)
        self.entry_h = tk.Entry(self.frame_left)
        self.entry_h.insert(0, "1800")
        self.entry_h.grid(row=4, column=1)

        tk.Label(self.frame_left, text="밴드간격").grid(row=5, column=0)
        self.entry_band = tk.Entry(self.frame_left)
        self.entry_band.insert(0, "1910")
        self.entry_band.grid(row=5, column=1)

        tk.Label(self.frame_left, text="전차선 높이에서 수평파이프까지 거리").grid(row=6, column=0)
        self.entry_registerarm_height = tk.Entry(self.frame_left)
        self.entry_registerarm_height.insert(0, "600")
        self.entry_registerarm_height.grid(row=6, column=1)

        tk.Label(self.frame_left, text="전주면과 브래킷피팅까지의 거리").grid(row=7, column=0)
        self.entry_bracket_to_mast_distance = tk.Entry(self.frame_left)
        self.entry_bracket_to_mast_distance.insert(0, "200")
        self.entry_bracket_to_mast_distance.grid(row=7, column=1)

        tk.Label(self.frame_left, text="레일면에서 브래킷 피팅까지 높이").grid(row=8, column=0)
        self.entry_rl_to_slopepipoe_height = tk.Entry(self.frame_left)
        self.entry_rl_to_slopepipoe_height.insert(0, "4970")
        self.entry_rl_to_slopepipoe_height.grid(row=8, column=1)

        tk.Label(self.frame_left, text="전차선 높이").grid(row=9, column=0)
        self.entry_cw_height = tk.Entry(self.frame_left)
        self.entry_cw_height.insert(0, "5080")
        self.entry_cw_height.grid(row=9, column=1)

        tk.Label(self.frame_left, text="레일면에서 전주 상단까지 높이").grid(row=10, column=0)
        self.entry_mast_height = tk.Entry(self.frame_left)
        self.entry_mast_height.insert(0, "7140")
        self.entry_mast_height.grid(row=10, column=1)

        tk.Label(self.frame_left, text="브래킷 타입").grid(row=11, column=0)
        self.entry_bracket_type = tk.Entry(self.frame_left)
        self.entry_bracket_type.insert(0, "O")
        self.entry_bracket_type.grid(row=11, column=1)

        # 이미지 불러오기 (참고용)
        img = Image.open(r"C:\Users\Administrator\Pictures\캡쳐\reference.png")  # 참고용 이미지 파일 경로
        img = img.resize((700, 700))  # 크기 조정
        self.photo = ImageTk.PhotoImage(img)
        tk.Label(self.frame_right, image=self.photo).pack()

        # 버튼
        tk.Button(self, text="계산하기", command=self.run_calculation).grid(row=15, column=0)
        tk.Button(self, text="DXF 저장", command=self.save_dxf).grid(row=15, column=1)
        tk.Button(self, text="시각화", command=self.show_plot).grid(row=15, column=2)
        tk.Button(self, text="종료", command=self.destroy).grid(row=15, column=3)

    def run_calculation(self):
        # 여기서 entry 값들을 가져와 계산 함수에 전달
        l = float(self.entry_l.get())
        stagger = float(self.entry_stagger.get())
        e = float(self.entry_e.get())
        f = float(self.entry_f.get())
        h = float(self.entry_h.get())
        band = float(self.entry_band.get())

        bracket_to_mast_distance = float(self.entry_bracket_to_mast_distance.get())
        rl_to_slopepipoe_height = float(self.entry_rl_to_slopepipoe_height.get())
        cw_height = float(self.entry_cw_height.get())
        cw_point = (stagger, cw_height)
        mast_height =  float(self.entry_mast_height.get())
        mw_point = (stagger, cw_height + e)

        bracket_type = self.entry_bracket_type.get()
        registerarm_height = float(self.entry_registerarm_height.get())
        target_y = cw_height + registerarm_height

        # 계산
        vertical = e + f - 110 + 70  # 1700
        horizontal = l - bracket_to_mast_distance + stagger  # 2450
        slope_pipe_l = (horizontal ** 2 + vertical ** 2 - 110 ** 2) ** 0.5
        theta = math.atan(vertical / horizontal) + math.atan(110 / slope_pipe_l)

        slope_start = -l + bracket_to_mast_distance, rl_to_slopepipoe_height + f

        # 끝점에서 50mm 이격
        # 경사파이프 끝점 (정확한 좌표)
        slope_end = slope_start[0] + slope_pipe_l * math.cos(theta), slope_start[1] + slope_pipe_l * math.sin(theta)

        top_start = slope_start[0], slope_start[1] + h
        # 끝점에서 50mm 이격 (연장선 방향)
        top_end = slope_end[0] + 50 * math.cos(theta + math.pi / 2), slope_end[1] + 50 * math.sin(theta + math.pi / 2)

        # Top tube 길이 (시작점 (0,h) ~ 끝점 (x2,y2))
        toptube_l = calculate_distance(top_start, top_end)

        # 수평파이프 시작점 구하기
        d = (target_y - slope_start[1] - 55 * math.sin(theta - math.pi / 2)) / math.sin(theta)  # 경사피이프에서 수평파이프 시작점까지 거리
        registerarm_cross_point = slope_start[0] + d * math.cos(theta), slope_start[1] + d * math.sin(theta)
        registerarm_start_point = registerarm_cross_point[0] + 55 * math.cos(theta - math.pi / 2), \
                                  registerarm_cross_point[1] + 55 * math.sin(theta - math.pi / 2)
        registerarm_end_point = ()
        if bracket_type == 'I':
            registerarm_end_point = 0 + stagger - 600 + 100, registerarm_start_point[1]
        elif bracket_type == 'O':
            registerarm_end_point = 0 + stagger + 1200 + 100 + 75, registerarm_start_point[1]
        registerarm_l = calculate_distance(registerarm_start_point, registerarm_end_point)

        # 보조파이프(rigid_suspenssion)
        # 시작점
        xvdd = slope_end[0] + 400 * math.cos(theta + math.pi), slope_end[1] + 400 * math.sin(theta + math.pi)
        rigid_suspenssion_start = xvdd[0] + 50 * math.cos(theta - math.pi / 2), xvdd[1] + 50 * math.sin(
            theta - math.pi / 2)

        # 끝점
        dsgd = registerarm_end_point[0] + 500 * math.cos(math.pi), registerarm_end_point[1] + 500 * math.sin(math.pi)
        rigid_suspenssion_end = dsgd[0] + 50 * math.cos(math.pi / 2), dsgd[1] + 50 * math.sin(math.pi / 2)
        rigid_suspenssion_l = calculate_distance(rigid_suspenssion_start, rigid_suspenssion_end)

        # 사각파이프(aux strut tube)
        aux_strut_tube_start, aux_strut_tube_end = cal_aux_struct_tube(slope_start, slope_end, top_start, top_end, theta)
        aux_strut_tube_l = calculate_distance(aux_strut_tube_start, aux_strut_tube_end)

        # 도면출력
        self.data = l, cw_point, mw_point, rl_to_slopepipoe_height, mast_height , slope_start,slope_end , top_start, top_end, registerarm_start_point, registerarm_end_point, rigid_suspenssion_start,rigid_suspenssion_end , aux_strut_tube_start, aux_strut_tube_end
        self.result = slope_pipe_l, theta, toptube_l, registerarm_l, rigid_suspenssion_l, aux_strut_tube_l
        messagebox.showinfo(
            "결과",
            f"경사파이프 길이: {slope_pipe_l * 0.001:.2f}m\n"
            f"경사파이프 각도: {math.degrees(theta):.2f}도\n"
            f"상부파이프 길이: {toptube_l * 0.001:.2f}m\n"
            f"경사파이프와 수평파이프까지 거리 L: {d * 0.001:.2f}m\n"
            f"수평파이프 길이 L: {registerarm_l * 0.001:.2f}m\n"
            f"보조파이프 길이 L: {rigid_suspenssion_l * 0.001:.2f}m\n"
            f"사각파이프 길이 L: {aux_strut_tube_l * 0.001:.2f}m"
        )

    def save_dxf(self):
        export_dxf(self.data)
        messagebox.showinfo("DXF 저장", "c:/temp/structure.dxf 로 저장되었습니다.")

    def show_plot(self):
        plot(self.data, self.result)

if __name__ == "__main__":
    app = MAINAPP()
    app.mainloop()


