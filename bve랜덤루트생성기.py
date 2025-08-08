import random
import math
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
import os

from pycparser.c_ast import While

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
    def create_random_radius(min_radius):
        """
        일정 범위 내에서 무작위 반지름 생성 (100 단위).
        음수는 좌곡선, 양수는 우곡선.
        """
        MAX = min_radius * 2  # 현실적인 최대 반지름

        radius = random.randrange(min_radius, MAX + 100, 100)
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
    def __init__(self, max_track_position, min_radius, min_length):
        self.horizontal_radii = []
        self.vertical_pitches = []
        self.curve_segments = []
        self.pitch_segments = []
        self.max_track_position = max_track_position
        self.min_radius = min_radius
        self.min_length = min_length

    def create_horizontal_alignment(self, count):
        curves_with_sta = []
        self.horizontal_radii.clear()
        self.curve_segments.clear()

        sta = 0.0
        MAX_LENGTH = self.min_length * 10
        i = 0
        attemp = 100

        while i < attemp:
            start = sta
            length = random.randint(self.min_length, MAX_LENGTH)
            end = start + length
            if end > self.max_track_position:
                break  # 트랙 끝 넘으면 종료

            radius = RandomGenerator.create_random_radius(self.min_radius)
            cant = RandomGenerator.create_random_cant()

            curves_with_sta.append((start, BVECommandGenerator.create_curve(start, radius, cant)))

            curves_with_sta.append((end, BVECommandGenerator.create_curve(end, 0, 0)))

            self.horizontal_radii.append(abs(radius))
            self.curve_segments.append((start, end, radius, cant))

            sta = end + random.randint(self.min_length, MAX_LENGTH)
            i += 1

        # 정렬 후 명령어만 반환
        curves_with_sta.pop(0)
        self.curve_segments.pop(0)
        self.horizontal_radii.pop(0)
        curves_with_sta.sort(key=lambda x: x[0])
        return [cmd for _, cmd in curves_with_sta]

    def create_vertical_alignment(self, count):
        lines_with_sta = []
        self.pitch_segments.clear()
        self.vertical_pitches.clear()

        sta = 0.0
        MIN_LENGTH = 600
        MAX_LENGTH = 1500
        i = 0

        attemp = 100
        while i < attemp:
            # 일정 구간씩 sta를 증가시켜가며 pitch 삽입
            start = (sta // 25) * 25
            length = random.randint(MIN_LENGTH, MAX_LENGTH)
            end = start + length
            if end > self.max_track_position:
                break  # 종단선형의 끝을 넘으면 종료

            pitch = RandomGenerator.create_random_pitch() if i !=0 else 0.0
            command = BVECommandGenerator.create_pitch(start, pitch)

            lines_with_sta.append((start, command))
            self.vertical_pitches.append(abs(pitch))
            self.pitch_segments.append((start, pitch * 0.001))

            sta = end  # 다음 시작점
            i += 1

        self.pitch_segments.sort(key=lambda x: x[0])
        lines_with_sta.sort(key=lambda x: x[0])
        return [cmd for _, cmd in lines_with_sta]

    def is_overlapping(self, start, end, ranges, buffer=125):
        for s, e in ranges:
            if not (end + buffer <= s or start - buffer >= e):
                return True
        return False

    def print_alignment_stats(self):
        print(f'곡선 갯수: {len(self.horizontal_radii)}')
        if self.horizontal_radii:
            print(f'최소 곡선 반경: {min(self.horizontal_radii):.2f} m')
        print(f'종단 갯수: {len(self.vertical_pitches)}')
        if self.vertical_pitches:
            print(f'최대 기울기: {max(self.vertical_pitches):.2f} ‰')

    def export_curve_info(self, max_sta, interval=25, filepath="CURVE_INFO.TXT"):
        """
        25m 간격으로 곡선반경 출력 파일 생성

        :param max_sta: 최대 STA 값
        :param interval: 출력 간격 (기본 25m)
        :param filepath: 출력 파일 경로
        """
        # 곡선 반경 정보가 저장된 리스트가 없으므로 alignment 생성 시 구조 저장 필요
        # 예: self.curve_segments = [(start, end, radius, cant)]

        if not hasattr(self, "curve_segments"):
            print("[오류] self.curve_segments 데이터가 없습니다. create_horizontal_alignment()에서 저장 필요")
            return

        output_lines = []
        for sta in range(0, max_sta + 1, interval):
            radius = 0
            cant = 0
            for start, end, r, c in self.curve_segments:
                if start <= sta <= end:
                    radius = r
                    cant = c
                    break
            output_lines.append(f"{sta},{radius},{cant}")

        # 파일 저장
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines))
            print(f"[정보] 곡선 정보가 '{filepath}'에 저장되었습니다.")
        except Exception as e:
            print(f"[오류] 파일 저장 실패: {e}")

    def export_pitch_info(self, max_sta, interval=25, filepath="pitch_INFO.TXT"):
        if not hasattr(self, "pitch_segments") or not self.pitch_segments:
            print("[오류] pitch_segments 데이터가 없습니다.")
            return

        # STA 오름차순 정렬
        self.pitch_segments.sort(key=lambda x: x[0])

        output_lines = []
        current_pitch = 0
        for sta in range(0, max_sta + 1, interval):
            for start, p in reversed(self.pitch_segments):  # 역순 탐색
                if start <= sta:
                    current_pitch = p
                    break
            output_lines.append(f"{sta},{current_pitch:.6f}")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines))
            print(f"[정보] 기울기 정보가 '{filepath}'에 저장되었습니다.")
        except Exception as e:
            print(f"[오류] 파일 저장 실패: {e}")


class TerrainGerator:
    @staticmethod
    def create_terrain(MAX_TRACK_POSITION):
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
    def __init__(self, MAX_TRACK_POSITION) -> None:
        self.structures = []  # 터널/교량 결과 저장 리스트
        self.bridge_count = 0
        self.tunnel_count = 0
        self.max_track_position = MAX_TRACK_POSITION
    def define_structure(self, elevlist):

        # Read STATION and ELEVATION lists
        STATION = list(range(0, self.max_track_position + 1, 25))
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
            output.append(f"; {structure.name}")  # 구조물 이름 주석

            if structure.structure_type == '터널':
                output.append(BVECommandGenerator.create_wall(structure.start_sta, 0, -1, 51))
                output.append(BVECommandGenerator.create_dikeend(structure.start_sta, 0))
                output.append(BVECommandGenerator.create_wallend(structure.end_sta, 0))
                output.append(BVECommandGenerator.create_dike(structure.end_sta, 0, 0, 32))
            else:  # 교량
                output.append(BVECommandGenerator.create_wall(structure.start_sta, 0, -1, 28))
                output.append(BVECommandGenerator.create_dikeend(structure.start_sta, 0))
                output.append(BVECommandGenerator.create_wallend(structure.end_sta, 0))
                output.append(BVECommandGenerator.create_dike(structure.end_sta, 0, 0, 32))

            output.append("")  # 구조물 간 빈 줄

        return output

    def save_to_excel(self, output_path):
        from openpyxl import Workbook
        wb = Workbook()

        # 시트: 교량
        bridge_ws = wb.active
        bridge_ws.title = '교량'
        #bridge_ws.append(['교량명', '시점', '종점', '연장'])

        # 시트: 터널
        tunnel_ws = wb.create_sheet(title='터널')
        #tunnel_ws.append(['터널명', '시점', '종점', '연장'])

        for structure in self.structures:
            name = structure.name
            start = structure.start_sta
            end = structure.end_sta
            length = end - start

            if structure.structure_type == '교량':
                bridge_ws.append([name, start, end, length])
            elif structure.structure_type == '터널':
                tunnel_ws.append([name, start, end, length])

        wb.save(output_path)
        print(f"구조물 정보가 Excel 파일로 저장되었습니다: {output_path}")

    def print_structure_counts(self):
        self.bridge_count = sum(1 for s in self.structures if s.structure_type == '교량')
        self.tunnel_count = sum(1 for s in self.structures if s.structure_type == '터널')

        print(f'교량갯수 : {self.bridge_count}')
        print(f'터널갯수 : {self.tunnel_count}')

import math

class Vector2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def rotate(self, cosine_of_angle, sine_of_angle):
        x_new = cosine_of_angle * self.x - sine_of_angle * self.y
        y_new = sine_of_angle * self.x + cosine_of_angle * self.y
        self.x, self.y = x_new, y_new

    def copy(self):
        return Vector2(self.x, self.y)

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def copy(self):
        return Vector3(self.x, self.y, self.z)



class TrackCalculator:
    def __init__(self, curve_file: str, pitch_file: str, interval: float = 25):
        self.curve_data = self._read_curve_info(curve_file)
        self.pitch_data = self._read_pitch_info(pitch_file)
        self.interval = interval
        self.data = self._calculate_block()

    def _read_curve_info(self, filename):
        data = []
        with open(filename, 'r') as f:
            for line in f:
                if line.strip() == '' or line.startswith('#'):
                    continue
                sta_str, radius_str, cant = line.strip().split(',')
                data.append({'sta': float(sta_str), 'radius': float(radius_str)})
        data.sort(key=lambda d: d['sta'])
        return data

    def _read_pitch_info(self, filename):
        data = []
        with open(filename, 'r') as f:
            for line in f:
                if line.strip() == '' or line.startswith('#'):
                    continue
                sta_str, pitch_str = line.strip().split(',')
                data.append({'sta': float(sta_str), 'pitch': float(pitch_str)})
        data.sort(key=lambda d: d['sta'])
        return data


    def _calculate_block(self):
        direction = Vector2(x=0.0,y=1.0)
        position = Vector3(x=0.0, y=0.0, z=0.0)
        data = []
        for i in range(len(self.curve_data)):
            a = 0.0
            c = self.interval
            h = 0.0
            radius = self.curve_data[i]['radius']
            pitch = self.pitch_data[i]['pitch']

            data.append(position.copy())

            if radius != 0.0 and pitch != 0.0:
                d = self.interval
                p = pitch
                r = radius
                s = d / math.sqrt(1.0 + p * p)
                h = s * p
                b = s / abs(r)
                c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))

                a = 0.5 * np.sign(r) * b
                direction.rotate(math.cos(-a), math.sin(-a))
            elif radius != 0.0:
                d = self.interval
                r = radius
                b = d / abs(r)
                c = math.sqrt(2.0 * r * r * (1.0 - math.cos(b)))
                a = 0.5 * np.sign(r) * b
                direction.rotate(math.cos(-a), math.sin(-a))
            elif pitch != 0.0:
                p = pitch
                d = self.interval
                c = d / math.sqrt(1.0 + p * p)
                h = c * p

            TrackYaw = math.atan2(direction.x, direction.y)
            TrackPitch = math.atan(pitch)

            position.x += direction.x * c
            position.y += h
            position.z += direction.y * c

            if a != 0.0:
                direction.rotate(math.cos(-a), math.sin(-a))

        return data

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            for block in self.data:
                f.write(f"{block.x},{block.z},{block.y}\n")


def create_base_txt():
    base_txt = ''
    base_txt += 'Options.ObjectVisibility 1\n'
    base_txt += 'With Route\n'
    base_txt += '.comment 랜덤루트\n'
    base_txt += '.Elevation 0\n'
    base_txt += 'With Train\n'
    base_txt += 'With Structure\n'
    base_txt += '$Include(오브젝트.txt)\n'
    base_txt += '$Include(프리오브젝트.txt)\n'
    base_txt += '$Include(km_index.txt)\n'
    base_txt += '$Include(curve_index.txt)\n'
    base_txt += '$Include(pitch_index.txt)\n'
    base_txt += 'With Track\n'
    base_txt += '$Include(전주.txt)\n'
    base_txt += '$Include(전차선.txt)\n'
    base_txt += '$Include(km_post.txt)\n'
    base_txt += '$Include(curve_post.txt)\n'
    base_txt += '$Include(pitch_post.txt)\n'
    base_txt += '$Include(신호.txt)\n'
    base_txt += '$Include(통신.txt)\n'
    base_txt += '0,.back 0;,.ground 0;,.dike 0;0;2;,.railtype 0;9;\n'
    base_txt += '0,.sta START STATION;\n'
    base_txt += '100,.stop 0;\n'
    return base_txt

def estimate_alignment_count(length_m, avg_spacing=1000, max_count=20, difficulty_factor=1.0):
    count = int((length_m / avg_spacing) * difficulty_factor)
    return min(max_count, max(1, count))

class AlignmentApp:
    def __init__(self, root):
        self.designspeed: float = 0.0
        self.root = root
        self.root.title("선형 및 구조물 자동 생성기")
        self.root.geometry("700x600")

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="저장 경로 선택").pack()
        self.path_entry = tk.Entry(self.root, width=80)
        self.path_entry.pack()
        tk.Button(self.root, text="폴더 선택", command=self.choose_folder).pack()

        tk.Button(self.root, text="선형 생성 시작", command=self.generate_alignment).pack(pady=10)

        self.log = scrolledtext.ScrolledText(self.root, width=80, height=25)
        self.log.pack()

    def log_write(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.root.update()

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)

    def input_velocity(self):
        # float 값 입력 받기
        while True:
            value = simpledialog.askstring("설계속도 입력", "설계속도를 입력하세요 (예: 150):")
            if value is None:  # 사용자가 취소를 눌렀을 때
                return False
            try:
                self.designspeed = float(value)
                break
            except ValueError:
                messagebox.showerror("입력 오류", "숫자(float) 형식으로 입력하세요.")

        self.log_write(f"설계속도 입력 완료: {self.designspeed}")

    def define_track_condition(self):
        max_track_length = random.randint(10000, 20000)
        curve_length = self.designspeed * 0.5
        if self.designspeed <= 70:
            min_radius = 400
            max_slope = 35
            curve_length = 40
        elif self.designspeed <= 120:
            min_radius = 700
            max_slope = 35
            curve_length = 60

        elif self.designspeed <= 150:
            min_radius = 1100
            max_slope = 35
            curve_length = 80
        elif self.designspeed <= 200:
            min_radius = 1900
            max_slope = 35
            curve_length = 100
        elif self.designspeed <= 250:
            min_radius = 2900
            max_slope = 35
            curve_length = 130
        elif self.designspeed <= 300:
            min_radius = 4500
            max_slope = 35
            curve_length = 150
        elif self.designspeed <= 350:
            min_radius = 6100
            max_slope = 35
            curve_length = 180
        elif self.designspeed <= 400:
            min_radius = 6100
            max_slope = 35
            curve_length = 200
        else:
            min_radius = 6100
            max_slope = 25
            curve_length = curve_length
        return max_track_length, min_radius, max_slope, curve_length

    def generate_alignment(self):
        try:
            self.input_velocity()
            folder = self.path_entry.get()
            if not folder:
                messagebox.showerror("오류", "저장 경로를 지정해주세요.")
                return

            self.log_write("생성 중...")
            max_track_length, min_radius, max_slope, curve_length = self.define_track_condition()
            while True:
                base_txt = create_base_txt()

                count_horizon = estimate_alignment_count(max_track_length)
                count_vertical = estimate_alignment_count(max_track_length, 1500)

                align_gen = AlignmentGenerator(max_track_length, min_radius, curve_length)
                elevation, nori, elevation_list = TerrainGerator.create_terrain(max_track_length)

                struct_gen = StructureGenerator(max_track_length)
                struct_gen.define_structure(elevation_list)
                out = struct_gen.create_structuesystax()

                base_txt += "\n,;평면선형\n" + '\n'.join(align_gen.create_horizontal_alignment(count_horizon)) + "\n"
                base_txt += "\n,;종단선형\n" + '\n'.join(align_gen.create_vertical_alignment(count_vertical)) + "\n"
                base_txt += "\n,;구조물\n" + '\n'.join(out) + "\n"
                base_txt += "\n,;표고\n" + '\n'.join(elevation) + "\n"
                base_txt += "\n,;사면\n" + ''.join(f"{a},{b}\n" for a, b in nori) + "\n"

                struct_gen.print_structure_counts()
                if struct_gen.bridge_count != 0 and struct_gen.tunnel_count != 0:
                    break

            base_txt += "\n,;노선 종점\n"
            base_txt += f"{max_track_length},.sta END STATION;\n"
            base_txt += f"{max_track_length + 100},.stop 0;\n"

            align_gen.print_alignment_stats()

            # 저장
            txtfolder = 'c:/temp/'
            csv_path = os.path.join(folder, "테스트.csv")
            curve_path = os.path.join(txtfolder, "CURVE_INFO.TXT")
            pitch_path = os.path.join(txtfolder, "pitch_INFO.TXT")
            coord_path = os.path.join(txtfolder, "bve_coordinates.TXT")
            excel_path = os.path.join(txtfolder, "구조물.xlsx")

            align_gen.export_curve_info(max_track_length, 25, curve_path)
            align_gen.export_pitch_info(max_track_length, 25, pitch_path)

            tc = TrackCalculator(curve_path, pitch_path, interval=25)
            tc.save_to_file(coord_path)

            struct_gen.save_to_excel(excel_path)

            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(base_txt)

            self.log_write("✔ 선형 생성 완료")
            self.log_write(f'✔ 노선연장 : {max_track_length * 0.001}km')
            self.log_write(f"✔ 저장 완료: {csv_path}")
            self.log_write(f"✔ 구조물 정보: {excel_path}")
            self.log_write(f"✔ 좌표 파일: {coord_path}")
        except Exception as e:
            messagebox.showerror("에러 발생", str(e))
            self.log_write(f"❌ 에러: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AlignmentApp(root)
    root.mainloop()
