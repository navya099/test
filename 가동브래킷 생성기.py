import tkinter as tk
import json
import ezdxf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import math
from AutoCAD.point2d import Point2d
from AutoCAD.line import Line2d
from bulgesegment import BulgeSegment
from polyline import Polyline
import numpy as np
import os

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ---------- 클래스 ----------
class Pipe(Line2d):
    def __init__(self, point1: Point2d, point2: Point2d, color="green", label=None):
        super().__init__(point1, point2)
        self.color = color
        self.label = label
        self.artist = None

    def draw(self, ax):
        line, = ax.plot([self.start.x, self.end.x], [self.start.y, self.end.y], color=self.color)
        self.artist = line
        if self.label:
            ax.text((self.start.x + self.end.x)/2, (self.start.y +self.end.y)/2, self.label,
                    fontsize=9, ha='center', color=self.color)

    def remove(self):
        if self.artist:
            self.artist.remove()
            self.artist = None

class SteadyARM(Polyline):
    def __init__(self, length: float,height: float, origin=Point2d(0,0),direction: int=1, color="green", label=None):
        self.color = color
        self.label = label
        self.artist = None
        self.direction = direction
        p2 = origin.moved(-math.pi/ 2 , height)
        line1 = Line2d(origin,p2)
        if self.direction == 1:
            p3 = p2.moved(0, length)
            bulge = -0.15
        else:
            p3 = p2.moved(math.pi, length)
            bulge = 0.15

        bulgearc = BulgeSegment(p2, p3, bulge)
        segments = [line1,bulgearc]
        super().__init__(segments)

    import numpy as np

    def draw(self, ax):
        for seg in self.segments:
            if isinstance(seg, BulgeSegment) and seg.bulge != 0:
                # 호를 샘플링해서 그리기

                angles = np.linspace(seg.start_angle, seg.end_angle, 50)
                xs = seg.center.x + seg.radius * np.cos(angles)
                ys = seg.center.y + seg.radius * np.sin(angles)
                ax.plot(xs, ys, color=self.color)
            else:
                # 직선은 그대로
                ax.plot([seg.start.x, seg.end.x],
                        [seg.start.y, seg.end.y],
                        color=self.color)

        if self.label:
            mid = self.segments[-1].end
            ax.text(mid.x, mid.y, self.label,
                    fontsize=9, ha='center', color=self.color)
    @property
    def end_point(self):
        return self.segments[-1].end

class MAST(Line2d):
    def __init__(self, mast_type, width, p1, p2):
        super().__init__(p1, p2)
        self.mast_type = mast_type
        self.width = width
        self.artists = []

    @property
    def height(self):
        return self.length

    def draw_centerline(self, ax):
        line, = ax.plot([self.start.x, self.end.x], [self.start.y, self.end.y], 'r--',
                        label=f"{self.mast_type} Centerline")
        self.artists.append(line)

    def draw_outline(self, ax):
        coords = [
            ([self.start.x - self.width/2, self.end.x - self.width/2], [self.start.y, self.end.y]),
            ([self.start.x + self.width/2, self.end.x + self.width/2], [self.start.y, self.end.y]),
            ([self.start.x - self.width/2, self.start.x + self.width/2], [self.end.y, self.end.y]),
            ([self.start.x - self.width/2, self.start.x + self.width/2], [self.end.y, self.end.y]),
        ]
        for x, y in coords:
            line, = ax.plot(x, y, 'skyblue')
            self.artists.append(line)

    def remove(self):
        for artist in self.artists:
            artist.remove()
        self.artists.clear()


# ---------- 메인 GUI ----------
class PipeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Slider Control")
        self.geometry("400x1000")

        # Plot 창
        self.plot_root = tk.Toplevel()
        self.plot_root.title("Plot Window")
        self.plot_root.geometry("600x900")

        self.fig, self.ax = plt.subplots()
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar_frame = tk.Frame(self.plot_root)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        NavigationToolbar2Tk(self.canvas, toolbar_frame)

        # 슬라이더 생성
        self.create_slider("전차선높이", 1, 10, 0.1, 5.2)
        self.create_slider("가고", 0, 2, 0.01, 0.96)
        self.create_slider("건식게이지", 0, 10, 0.01, 3.0)
        self.create_slider("전주길이", 1, 20, 0.1, 9)
        self.create_slider("메인파이프길이", 0.1, 10, 0.1, 3.5)
        self.create_slider("메인파이프y", 0, 10, 0.1, 5.96)
        self.create_slider("경사파이프y", 0, 10, 0.01, 4.96)
        self.create_slider("경사파이프x", -10, 10, 0.01, 0)
        self.create_slider("보조파이프길이", 0.1, 10, 0.1, 2.5)
        self.create_slider("보조파이프x", -10, 10, 0.1, -1.3)
        self.create_slider("곡선당김금구x", -10, 10, 0.1, 0)
        self.create_slider("곡선당김금구방향", -1, 1, 2, 1)

        # 저장/로드 버튼 추가
        btn_save = tk.Button(self, text="세팅 저장", command=self.save_settings)
        btn_save.pack(pady=5)
        btn_load = tk.Button(self, text="세팅 불러오기", command=self.load_settings)
        btn_load.pack(pady=5)

        btn = tk.Button(self, text="DXF 저장", command=self.save_dxf)
        btn.pack(pady=10)


        self.update_plot()

    def save_settings(self):
        settings = {}
        # 모든 슬라이더 값 저장
        for attr in dir(self):
            if attr.startswith("slider_"):
                slider = getattr(self, attr)
                settings[attr] = slider.get()
        # JSON 파일로 저장
        with open("c:/temp/settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print("세팅 저장 완료!")

    def load_settings(self):
        if not os.path.exists("c:/temp/settings.json"):
            print("저장된 세팅 파일이 없습니다.")
            return
        with open("c:/temp/settings.json", "r", encoding="utf-8") as f:
            settings = json.load(f)
        # 슬라이더 값 복원
        for attr, value in settings.items():
            if hasattr(self, attr):
                slider = getattr(self, attr)
                slider.set(value)
        self.update_plot()
        print("세팅 불러오기 완료!")

    def create_slider(self, label, from_, to, resolution, init):
        slider = tk.Scale(self, label=label, from_=from_, to=to,
                          resolution=resolution, orient="horizontal",
                          length=300, command=self.update_plot)
        slider.set(init)
        slider.pack(padx=10, pady=5)
        setattr(self, f"slider_{label}", slider)

    def create_text_input_form(self, title: str, default_value=0.0):
        label = tk.Label(self, text=title, font=("Malgun Gothic", 12))
        label.pack(padx=10, pady=5)
        text_var = tk.DoubleVar(value=default_value)
        entry = tk.Entry(self, textvariable=text_var, width=30)
        entry.pack(padx=10, pady=5)
        setattr(self, f"text_var{title}", text_var)

    def update_plot(self, val=None):
        self.ax.clear()
        self.ax.set_xlim(-5, 5)
        self.ax.set_ylim(0, 12)

        system_height = float(self.slider_가고.get())
        contact_height = float(self.slider_전차선높이.get())
        rail_level = Point2d(0,0)
        trolly_wire = Point2d(0, contact_height)
        messanger_wire = Point2d(0, trolly_wire.y + system_height)
        pole_height = float(self.slider_전주길이.get())
        gague = float(self.slider_건식게이지.get())
        mainpipe_l = float(self.slider_메인파이프길이.get())
        mainpipe_y = float(self.slider_메인파이프y.get())

        slopepipe_y = float(self.slider_경사파이프y.get())
        slopepipe_x = float(self.slider_경사파이프x.get())

        subpipe_l = float(self.slider_보조파이프길이.get())
        subpipe_x = float(self.slider_보조파이프x.get())

        steadyarm_x = float(self.slider_곡선당김금구x.get())
        steadyarm_dir = float(self.slider_곡선당김금구방향.get())
        # 전주
        p1 = Point2d(rail_level.x - gague,0)
        p2 = p1.moved(math.pi / 2, pole_height)

        self.mast = MAST("강관주", 0.264, p1=p1, p2=p2)
        self.mast.draw_centerline(self.ax)
        self.mast.draw_outline(self.ax)

        # 메인 파이프
        mps = Point2d(p1.x, mainpipe_y)
        mpe = mps.moved(0, mainpipe_l)
        self.main_pipe = Pipe(point1=mps,point2=mpe,color="green",label='주파이프')
        self.main_pipe.draw(self.ax)

        # 경사 파이프
        sps = Point2d(p1.x, slopepipe_y)
        spe = Point2d(slopepipe_x, mpe.y)
        self.slope_pipe = Pipe(point1=sps, point2=spe, color="skyblue", label='경사파이프')
        self.slope_pipe.draw(self.ax)

        # 보조 파이프
        subs = Point2d(subpipe_x, self.slope_pipe.get_y_from_x(subpipe_x))
        sube = subs.moved(0, subpipe_l)
        self.sub_pipe = Pipe(point1=subs, point2=sube, color="skyblue", label='수평파이프')
        self.sub_pipe.draw(self.ax)

        #곡선당김금구
        origin = Point2d(steadyarm_x, subs.y)
        self.stadyarm = SteadyARM(length=0.90,height=0.35,origin=origin,direction=steadyarm_dir,color='red',label=None)
        self.stadyarm.draw(self.ax)

        # 포인트 표시
        for point, label, color in [(rail_level, "RL", "black"), (trolly_wire, "TW", "red"), (messanger_wire, "MW", "blue")]:
            self.ax.scatter(point.x, point.y, color=color)
            self.ax.text(point.x, point.y, label, fontsize=12, ha='left', color=color)

        self.fig.canvas.draw_idle()

    def save_dxf(self):
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        # 메인 파이프 예시
        msp.add_line((self.main_pipe.start.x, self.main_pipe.start.y),
                     (self.main_pipe.end.x, self.main_pipe.end.y))
        msp.add_line((self.slope_pipe.start.x, self.slope_pipe.start.y),
                     (self.slope_pipe.end.x, self.slope_pipe.end.y))
        msp.add_line((self.sub_pipe.start.x, self.sub_pipe.start.y),
                     (self.sub_pipe.end.x, self.sub_pipe.end.y))
        msp.add_line((self.mast.start.x, self.mast.start.y),
                     (self.mast.end.x, self.mast.end.y))
        # BulgeSegment 예시
        for seg in self.stadyarm.segments:
            if isinstance(seg, BulgeSegment) and seg.bulge != 0:
                if self.stadyarm.direction == -1:
                    st = seg.start_angle
                    ed = seg.end_angle
                else:
                    st = seg.end_angle
                    ed = seg.start_angle
                msp.add_arc(center=(seg.center.x, seg.center.y),
                            radius=seg.radius,
                            start_angle=math.degrees(st),
                            end_angle=math.degrees(ed))
            else:
                msp.add_line((seg.start.x, seg.start.y),
                             (seg.end.x, seg.end.y))

        doc.saveas("c:/temp/pipe_system.dxf")


# 실행
if __name__ == "__main__":
    app = PipeApp()
    app.mainloop()