import tkinter as tk
from tkinter import ttk, messagebox
import os

class Translater:
    @staticmethod
    def translate(x=0,y=0,z=0):
        return f'Translate, {x}, {y}, {z}\n'
    @staticmethod
    def translateall(x=0,y=0,z=0):
        return f'TranslateAll, {x}, {y}, {z}\n'
    @staticmethod
    def mirror(x=0,y=0,z=0):
        return f'Mirror, {x}, {y}, {z}\n'
    @staticmethod
    def mirrorall(x=0,y=0,z=0):
        return f'MirrorAll, {x}, {y}, {z}\n'

class Constructor:
    def __init__(self, app):
        self.app = app
        self.platformlines = []
        self.walllines = []

    def get_files(self):
        #승강장 불러오기
        self.platformlines = self.app.get_file_contents('승강장.csv')
        #벽체
        self.walllines = self.app.get_file_contents('벽체.csv')

    def construct_platform(self):
        for i, line in enumerate(self.platformlines):
            if '{linedistance}' in line:
                line = line.replace('{linedistance}', str(self.app.width.get()))
            if '{length}' in line:
                line = line.replace('{length}', str(self.app.length.get()))
            self.platformlines[i] = line
        self.app.lines += "".join(self.platformlines) +"\n"

    def construct_wall(self):
        """
        벽체 작성
        linedistance: 선로중심간격
        length: 구조물 연장
        width:승강장 폭
        formtoraildistance: 승강장 연단거리
        """
        # 벽체두께
        wallwidth = 0.7
        # 내부벽체 좌표
        sp = self.app.linedistance.get() / 2 + self.app.width.get() + self.app.formtoraildistance.get()  # 7.9
        # 공동구 좌표 7.5
        tray = sp - 0.4
        # 외부벽체 좌표 8.6
        wallout = sp + wallwidth
        # 상부헌치 좌표 -7.4
        tophunch = tray - 0.1
        for i, line in enumerate(self.walllines):
            if '{tray}' in line:
                line = line.replace('{tray}', str(tray))
            if '{length}' in line:
                line = line.replace('{length}', str(self.app.length.get()))
            if '{tophunch}' in line:
                line = line.replace('{tophunch}', str(tophunch))
            if '{wallout}' in line:
                line = line.replace('{wallout}', str(wallout))
            if '{sp}' in line:
                line = line.replace('{sp}', str(sp))
            self.walllines[i] = line
        self.app.lines += "".join(self.walllines) + '\n'

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lines = ''
        self.title("BVE 플랫폼 생성기")
        self.geometry("500x400")

        # 변수 선언
        self.linedistance = tk.DoubleVar(value=4.0)
        self.length = tk.DoubleVar(value=100.0)
        self.width = tk.DoubleVar(value=3.0)
        self.formtoraildistance = tk.DoubleVar(value=1.7)

        #현재 파이선 파일이 실행되는 경로 가져오기
        self.workdirectory = os.getcwd()
        # UI 생성
        self.create_widgets()

    def create_widgets(self):
        # linedistance
        self.add_slider("선로중심간격 (m)", self.linedistance, 2, 10)
        # length
        self.add_slider("길이 (m)", self.length, 10, 500)
        # width
        self.add_slider("승강장 폭 (m)", self.width, 1, 10)

        # formtoraildistance
        frm = ttk.Frame(self)
        frm.pack(pady=10, fill="x")
        ttk.Label(frm, text="승강장 연단거리 (m):").pack(side="left", padx=5)
        ttk.Entry(frm, textvariable=self.formtoraildistance, width=10).pack(side="left")

        # 실행 버튼
        ttk.Button(self, text="생성", command=self.generate).pack(pady=20)

    def add_slider(self, label, variable, frm, to):
        frame = ttk.Frame(self)
        frame.pack(pady=5, fill="x")

        ttk.Label(frame, text=label).pack(anchor="w")

        scale = ttk.Scale(frame, variable=variable, from_=frm, to=to, orient="horizontal")
        scale.pack(side="left", expand=True, fill="x", padx=5)

        entry = ttk.Entry(frame, textvariable=variable, width=8)
        entry.pack(side="right", padx=5)

    def get_file_contents(self, filename):

        filepath = os.path.join(self.workdirectory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()

    def export(self,filename):
        filepath = os.path.join(self.workdirectory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.lines)
            f.close()

    def generate(self):

        tranlatex = self.linedistance.get() / 2 #선로중심간격 /2

        #줄 초기화
        self.lines = ""

        #가공 시작
        constructor = Constructor(self)
        constructor.get_files() #필수파일 수집

        #하선승강장
        constructor.construct_platform()
        #트랜스레이트 적용
        self.lines += Translater.translate(x=-(self.formtoraildistance.get() + tranlatex), y=0, z=0)

        #상선 승강장
        constructor.construct_platform()
        self.lines += Translater.mirror(x=1, y=0, z=0)
        self.lines += Translater.translate(x=(self.formtoraildistance.get() + tranlatex), y=0, z=0)

        #벽체생성
        #하선
        constructor.construct_wall()
        #상선
        constructor.construct_wall()
        #미러
        self.lines += Translater.mirror(x=1, y=0, z=0)
        #전체객체 선로중심간격 이동
        self.lines += Translater.translateall(x=tranlatex, y=0, z=0)

        #추출
        self.export("test.csv")

        messagebox.showinfo('생성 및 저장 완료',f'{self.workdirectory}에 성공적으로 저장되었습니다.')

if __name__ == "__main__":
    app = App()
    app.mainloop()
