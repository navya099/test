import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import math

MIN_TRACK_POSITION = 600  # 600m
MAX_TRACK_POSITION_DEFAULT = 10000  # 기본 10km
# 랜덤 노선의 길이 범위 설정
MAX_TRACK_POSITION = 10000  # 10km
MIN_RADIUS = 600  # 최소곡선반경

class BVECommandGenerator:

    @staticmethod
    def create_rail(track_position, rail_index, x_offset, y_offset, railobj_index):
        return f'{track_position},.rail {rail_index};{x_offset};{y_offset};{railobj_index};'

    @staticmethod
    def create_curve(track_position, radius, cant):
        return f'{track_position},.curve {radius};{cant};'

    @staticmethod
    def create_pitch(track_position, pitch):
        return f'{track_position},.pitch {pitch};'

    @staticmethod
    def create_height(track_position, height):
        return f'{track_position},.height {height};'
    
    @staticmethod
    def create_dike(track_position, rail_index, direction, dike_object_index):
        return f'{track_position},.dike {rail_index};{direction};{dike_object_index};'
    
    @staticmethod
    def create_dikeend(track_position, rail_index):
        return f'{track_position},.dikeend {rail_index};'
    
    @staticmethod
    def create_wall(track_position, rail_index, direction, wall_object_index):
        return f'{track_position},.wall {rail_index};{direction};{wall_object_index};'


    @staticmethod
    def create_wallend(track_position, rail_index):
        return f'{track_position},.wallend {rail_index};'
    
    @staticmethod
    def create_ground(track_position, ground_object_index):
        return f'{track_position},.ground {ground_object_index};'
    
class RandomGenerator:

    @staticmethod
    def create_random_track_position():
        while True:
            start_track = random.randrange(MIN_TRACK_POSITION, MAX_TRACK_POSITION)
            end_track = random.randrange(MIN_TRACK_POSITION, MAX_TRACK_POSITION)
            if start_track < end_track:
                return start_track, end_track

    @staticmethod
    def create_random_radius():
        while True:
            radius = random.randrange(0, 1000) // 100 * 100
            if radius > MIN_RADIUS:
                if random.choice([True, False]):
                    radius = -radius  # 좌곡선
                return radius

    @staticmethod
    def create_random_cant():
        return random.randrange(0, 180) // 10 * 10

    @staticmethod
    def create_random_pitch():
        return round(random.uniform(-35, 35), 1)

    @staticmethod
    def generate_random_elevation(length=10000, step=25):
        elevation = 0
        result = []
        for pos in range(0, length, step):
            slope = random.uniform(-0.3, 0.3)  # 0.3‰ 단위 기울기
            elevation += slope * step
            result.append(round(elevation, 2))
        return result
    
class AlignmentGenerator:

    @staticmethod
    def create_horizontal_alignment(count):
        lines = []
        used_ranges = []
        for _ in range(count):
            attempt = 0
            while True:
                start, end = RandomGenerator.create_random_track_position()
                radius = RandomGenerator.create_random_radius()
                length = end - start
                ia = length / radius
                if ia < math.pi / 2  and not AlignmentGenerator.is_overlapping(start, end, used_ranges):
                    used_ranges.append((start, end))
                    break
                if attempt > 100:  # 무한 루프 방지
                    raise RuntimeError("곡선 생성 실패: 조건에 맞는 위치 부족")

            cant = RandomGenerator.create_random_cant()
            scurve = BVECommandGenerator.create_curve(start, radius, cant)
            ecurve = BVECommandGenerator.create_curve(end, 0, 0)
            lines.append(scurve)
            lines.append(ecurve)
        return lines

    @staticmethod
    def create_vertical_alignment(count):
        lines = []
        for _ in range(count):
            start, _ = RandomGenerator.create_random_track_position()
            pitch = RandomGenerator.create_random_pitch()
            syntax = BVECommandGenerator.create_pitch(start, pitch)
            lines.append(syntax)
        return lines

    @staticmethod
    def is_overlapping(start, end, ranges, buffer=125):  # 버퍼는 m 단위
        for s, e in ranges:
            if not (end + buffer <= s or start - buffer >= e):
                return True
        return False


class TerrainGerator:
    @staticmethod
    def create_terrain():
        #25간격으로 지형 생성
        lines = []
        nori = []
        elevlist = RandomGenerator.generate_random_elevation(MAX_TRACK_POSITION, step=25)
        for i , elev in enumerate(elevlist):
            pos = i * 25
            height = BVECommandGenerator.create_height(pos, elev)
            ground =  BVECommandGenerator.create_ground(pos , 0 if elev > 1 else 3 )
            rail = TerrainGerator.create_nori(pos, elev)
            lines.append(height)
            lines.append(ground)
            nori.append(rail)
        return lines, nori , elevlist
    
    @staticmethod
    def create_nori(pos, elev):
        x = elev * 1.5
        rail1 = BVECommandGenerator.create_rail(pos, 200,-x, -elev, 88)
        rail2 = BVECommandGenerator.create_rail(pos, 201, x, -elev, 87)
        return [rail1 ,rail2]
    
class Structure:
    def __init__(self, name, structuretype, start_sta, end_sta) -> None:
        self.name = name
        self.structure_type = structuretype
        self.start_sta = start_sta
        self.end_sta = end_sta

class Bridge(Structure):
    def __init__(self, name, structuretype, start_sta, end_sta):
        super().__init__(name, structuretype, start_sta, end_sta)

class Tunnel(Structure):
    def __init__(self, name, structuretype, start_sta, end_sta):
        super().__init__(name, structuretype, start_sta, end_sta)

class StructureGenerator:
    def __init__(self) -> None:
        self.structures = []  # 터널/교량 결과 저장 리스트

    def define_structure(self, elevlist):

        # Read STATION and ELEVATION lists
        STATION = list(range(0, MAX_TRACK_POSITION + 1, 25))
        ELEVATION = elevlist

        # Initialize group lists and counters
        OUT = []
        b_groups = []
        t_groups = []
        bcount = 1
        tcount = 1
        current_group = []
        consecutive_elevations = 0

        # Loop through ELEVATION list and group consecutive values
        for i in range(len(ELEVATION)):
            pos = i * 25
            # Check if value is greater than or equal to 12
            if ELEVATION[i] >= 12:
                current_group.append(STATION[i])
                consecutive_elevations += 1
                # Check if next value is less than 12 or if at end of list
                if i == len(ELEVATION) - 1 or ELEVATION[i + 1] < 12:
                    if consecutive_elevations >= 6:
                        b_groups.append((f"b{bcount}", current_group[0], current_group[-1]))
                        bcount += 1
                    current_group = []
                    consecutive_elevations = 0
            # Check if value is less than or equal to -12
            elif ELEVATION[i] <= -12:
                current_group.append(STATION[i])
                consecutive_elevations += 1
                # Check if next value is greater than -12 or if at end of list
                if i == len(ELEVATION) - 1 or ELEVATION[i + 1] > -12:
                    if consecutive_elevations >= 6 and min(ELEVATION[i - len(current_group) + 1:i + 1]) <= -40:
                        t_groups.append((f"t{tcount}", current_group[0], current_group[-1]))
                        tcount += 1
                    current_group = []
                    consecutive_elevations = 0

        # Output lists of first and last STATION values for each group
        OUT = [
            [group[1] for group in b_groups],#교량 시점
            [group[2] for group in b_groups],#교량 종점
            [group[1] for group in t_groups],#터널 시점
            [group[2] for group in t_groups] #터널 종점
        ]

        # 구조물 객체 리스트에 터널/교량 추가
        for i in range(len(OUT[2])):
            self.structures.append(Tunnel(f'Tunnel_{i + 1}', '터널', OUT[2][i], OUT[3][i]))

        for i in range(len(OUT[0])):
            self.structures.append(Bridge(f'Bridge_{i + 1}', '교량', OUT[0][i], OUT[1][i]))

    def create_structuesystax(self):
        output = []
        for structure in self.structures:
            if structure.structure_type == '터널':
                output.append(BVECommandGenerator.create_wall(structure.start_sta, 0,  -1, 51))
                output.append(BVECommandGenerator.create_dikeend(structure.start_sta, 0))
                output.append(BVECommandGenerator.create_wallend(structure.end_sta, 0))
                output.append(BVECommandGenerator.create_dike(structure.end_sta, 0, 0, 32))
            else:  # 교량
                output.append(BVECommandGenerator.create_wall(structure.start_sta, 0, -1, 28))
                output.append(BVECommandGenerator.create_dikeend(structure.start_sta, 0))
                output.append(BVECommandGenerator.create_wallend(structure.end_sta, 0))
                output.append(BVECommandGenerator.create_dike(structure.end_sta, 0, 0, 32))  # 예시값

        return output


def create_base_txt():
    base_txt = ''
    base_txt += 'Options.ObjectVisibility 1\n'
    base_txt += 'With Route\n'
    base_txt += '.comment 랜덤루트\n'
    base_txt += '.Elevation 0\n'
    base_txt += 'With Train\n'
    base_txt += 'With Structure\n'
    base_txt += '$Include(오브젝트.txt)\n'
    base_txt += 'With Track\n'
    base_txt += '0,.back 0;,.ground 0;,.dike 0;0;2;\n'
    base_txt += '0,.sta START STATION;\n'
    base_txt += '100,.stop 0;\n'
    return base_txt

def estimate_alignment_count(length_m, avg_spacing=1000):
    return max(1, length_m // avg_spacing)

# --- GUI 코드 시작 ---

class RandomRouteGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("랜덤 루트 생성기")
        self.geometry("900x700")

        # 기본 변수들
        self.max_track_position = tk.IntVar(value=MAX_TRACK_POSITION_DEFAULT)
        self.horizon_spacing = tk.IntVar(value=1000)
        self.vertical_spacing = tk.IntVar(value=1500)

        # UI 구성
        self.create_widgets()

        # 저장용 텍스트 변수
        self.generated_text = ""

    def create_widgets(self):
        frame_top = ttk.Frame(self)
        frame_top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(frame_top, text="노선 길이(m):").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frame_top, textvariable=self.max_track_position, width=10).grid(row=0, column=1)

        ttk.Label(frame_top, text="평면선형 간격(m):").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        ttk.Entry(frame_top, textvariable=self.horizon_spacing, width=10).grid(row=0, column=3)

        ttk.Label(frame_top, text="종단선형 간격(m):").grid(row=0, column=4, sticky=tk.W, padx=(20,0))
        ttk.Entry(frame_top, textvariable=self.vertical_spacing, width=10).grid(row=0, column=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10)

        btn_generate = ttk.Button(btn_frame, text="루트 생성", command=self.generate_route)
        btn_generate.pack(side=tk.LEFT, padx=5)

        btn_save = ttk.Button(btn_frame, text="파일로 저장", command=self.save_file)
        btn_save.pack(side=tk.LEFT, padx=5)

        # 텍스트 출력 영역
        self.text_output = tk.Text(self, wrap=tk.NONE, font=("Consolas", 10))
        self.text_output.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 수평 스크롤바
        xscroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text_output.xview)
        xscroll.pack(fill=tk.X)
        self.text_output.config(xscrollcommand=xscroll.set)

        # 수직 스크롤바
        yscroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text_output.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_output.config(yscrollcommand=yscroll.set)

    def generate_route(self):
        try:
            max_pos = self.max_track_position.get()
            horizon_sp = self.horizon_spacing.get()
            vertical_sp = self.vertical_spacing.get()

            # 아래에 기존 랜덤 루트 생성 코드를 사용해서 텍스트 생성
            base_txt = create_base_txt()

            count_horizon_alignment = estimate_alignment_count(max_pos, horizon_sp)
            count_vertical_alignment = estimate_alignment_count(max_pos, vertical_sp)

            # 평면선형 생성 (함수는 기존 클래스에 맞게 수정 또는 복사 필요)
            lines_horizontal = AlignmentGenerator.create_horizontal_alignment(count_horizon_alignment)
            lines_vertical = AlignmentGenerator.create_vertical_alignment(count_vertical_alignment)
            elev_lines, nori_lines, elevation_list = TerrainGerator.create_terrain()

            base_txt += '\n,;평면선형\n'
            base_txt += '\n'.join(lines_horizontal) + '\n'

            base_txt += '\n,;종단선형\n'
            base_txt += '\n'.join(lines_vertical) + '\n'

            structuregenerator = StructureGenerator()
            structuregenerator.define_structure(elevation_list)
            out = structuregenerator.create_structuesystax()

            base_txt += '\n,;구조물\n'
            base_txt += '\n'.join(out) + '\n'

            base_txt += '\n,;표고\n'
            base_txt += '\n'.join(elev_lines) + '\n'

            base_txt += '\n,;사면\n'
            base_txt += ''.join(f"{a},{b}\n" for a, b in nori_lines) + '\n'

            base_txt += '\n노선 종점\n'
            base_txt += f'{max_pos},.sta END STATION;\n'
            base_txt += f'{max_pos + 100},.stop 0;'

            self.generated_text = base_txt

            self.text_output.delete('1.0', tk.END)
            self.text_output.insert(tk.END, base_txt)

            messagebox.showinfo("완료", "랜덤 루트 생성이 완료되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"생성 중 오류가 발생했습니다:\n{e}")

    def save_file(self):
        if not self.generated_text:
            messagebox.showwarning("경고", "먼저 '루트 생성' 버튼을 눌러 루트를 생성하세요.")
            return
        fpath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
            title="파일로 저장"
        )
        if fpath:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(self.generated_text)
                messagebox.showinfo("저장 완료", f"파일이 저장되었습니다:\n{fpath}")
            except Exception as e:
                messagebox.showerror("오류", f"파일 저장 중 오류가 발생했습니다:\n{e}")



if __name__ == "__main__":
    # 주의: 전체 기존 클래스(BVECommandGenerator 등)를 위에 붙여넣어야 정상 작동합니다.
    app = RandomRouteGUI()
    app.mainloop()