import random
import math
import numpy as np

# 랜덤 노선의 길이 범위 설정
MIN_TRACK_POSITION = 600  # 600m
MAX_TRACK_POSITION = 10000  # 10km

#선형 관련 전역변수
MIN_RADIUS = 600 #최소곡선반경

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
    def __init__(self):
        self.horizontal_radii = []
        self.vertical_pitches = []
        self.curve_segments = []
        self.pitch_segments = []

    def create_horizontal_alignment(self, count):
        curves = []  # (sta, command) 형식으로 저장
        used_ranges = []
        self.horizontal_radii.clear()
        self.curve_segments = []

        for i in range(count):
            attempt = 0
            while True:
                start, end = RandomGenerator.create_random_track_position()
                # 🔧 25의 배수로 조정
                start = (start // 25) * 25
                end = ((end + 24) // 25) * 25

                radius = RandomGenerator.create_random_radius()
                length = end - start
                ia = length / radius

                if ia < math.pi / 2 and not self.is_overlapping(start, end, used_ranges):
                    used_ranges.append((start, end))
                    break

                attempt += 1
                if attempt > 100:
                    print(f"[경고] {i + 1}번째 곡선 생성 실패: 조건에 맞는 위치 부족 (스킵됨)")
                    radius = 1000
                    cant = 0
                    curves.append((start, BVECommandGenerator.create_curve(start, radius, cant)))
                    curves.append((end, BVECommandGenerator.create_curve(end, 0, 0)))
                    self.horizontal_radii.append(abs(radius))
                    break

            if attempt <= 100:
                cant = RandomGenerator.create_random_cant()
                curves.append((start, BVECommandGenerator.create_curve(start, radius, cant)))
                curves.append((end, BVECommandGenerator.create_curve(end, 0, 0)))
                self.horizontal_radii.append(abs(radius))
                self.curve_segments.append((start, end, radius, cant))  # 곡선 구간 저장
        # STA 기준 정렬
        curves.sort(key=lambda x: x[0])



        # command만 추출
        return [cmd for _, cmd in curves]

    def create_vertical_alignment(self, count):
        lines_with_sta = []
        self.pitch_segments.clear()
        self.vertical_pitches.clear()

        for _ in range(count):
            start, _ = RandomGenerator.create_random_track_position()
            start = (start // 25) * 25

            pitch = RandomGenerator.create_random_pitch()
            command = BVECommandGenerator.create_pitch(start, pitch)
            lines_with_sta.append((start, command))
            self.vertical_pitches.append(abs(pitch))
            self.pitch_segments.append((start, pitch * 0.001))

        self.pitch_segments.sort(key=lambda x: x[0])
        lines_with_sta.sort(key=lambda x: x[0])  # ✅ 출력도 정렬

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
        bridge_count = sum(1 for s in self.structures if s.structure_type == '교량')
        tunnel_count = sum(1 for s in self.structures if s.structure_type == '터널')

        print(f'교량갯수 : {bridge_count}')
        print(f'터널갯수 : {tunnel_count}')

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
    base_txt += 'With Track\n'
    base_txt += '$Include(전주.txt)\n'
    base_txt += '$Include(전차선.txt)\n'
    base_txt += '0,.back 0;,.ground 0;,.dike 0;0;2;,.railtype 0;9;\n'
    base_txt += '0,.sta START STATION;\n'
    base_txt += '100,.stop 0;\n'
    return base_txt

def estimate_alignment_count(length_m, avg_spacing=1000):
    return max(1, length_m // avg_spacing)

#메인코드
# 기본 구문 생성
base_txt = create_base_txt()

# 평면 및 종단선형 갯수 설정
count_horizon_alignment = estimate_alignment_count(MAX_TRACK_POSITION) #평면선형은 기본값 1000
count_vertical_alignment = estimate_alignment_count(MAX_TRACK_POSITION, 1500) #구배만 1500간격

#선형 생성 클래스 생성
alignment_generator = AlignmentGenerator()

#지형 생성
elevation, nori , elevation_list = TerrainGerator.create_terrain()

#구조물
structuregenerator = StructureGenerator()
structuregenerator.define_structure(elevation_list)
out = structuregenerator.create_structuesystax()

#구문 생성
base_txt += '\n,;평면선형\n'
base_txt += '\n'.join(alignment_generator.create_horizontal_alignment(count_horizon_alignment))
base_txt += '\n'

base_txt += '\n,;종단선형\n'
base_txt += '\n'.join(alignment_generator.create_vertical_alignment(count_vertical_alignment))
base_txt += '\n'

base_txt += '\n,;구조물\n'
base_txt += '\n'.join(out)
base_txt += '\n'

base_txt += '\n,;표고\n'
base_txt += '\n'.join(elevation)
base_txt += '\n'

base_txt += '\n,;사면\n'
base_txt += ''.join(f"{a},{b}\n" for a, b in nori)
base_txt += '\n'

#구문작성

#종점
base_txt += '\n,;노선 종점\n'
base_txt += f'{MAX_TRACK_POSITION},.sta END STATION;\n'
base_txt += f'{MAX_TRACK_POSITION + 100},.stop 0;'

#결과출력
#선형
print(f'계산 완료: 노선 정보 출력')
alignment_generator.print_alignment_stats()
structuregenerator.print_structure_counts()
# 저장
structuregenerator.save_to_excel('c:/temp/구조물.xlsx')
filepath = r'D:\BVE\루트\Railway\Route\연습용루트\테스트.csv'
curvepath="c:/temp/CURVE_INFO.TXT"
pitchpath="c:/temp/pitch_INFO.TXT"
coordpath = "c:/temp/bve_coordinates.TXT"
alignment_generator.export_curve_info(MAX_TRACK_POSITION, interval=25, filepath=curvepath)
alignment_generator.export_pitch_info(MAX_TRACK_POSITION, interval=25, filepath=pitchpath)

#좌표저장
tc = TrackCalculator(curvepath, pitchpath, interval=25)
tc.save_to_file(coordpath)
print("트랙 좌표 계산 완료. bve_coordinates.txt 파일 생성됨.")

try:
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in base_txt.splitlines():
            f.write(line + '\n')
    print(f"저장 완료: {filepath}")

except IOError as ex:
    print(f"파일 저장 중 오류 발생: {ex}")
