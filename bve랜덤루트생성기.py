import random
import math

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
    def is_overlapping(start, end, ranges):
        for s, e in ranges:
            if not (end <= s or start >= e):  # 범위가 겹친다면
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
        bridge_start, tunnel_start = None, None

        for i, eleve in enumerate(elevlist):
            pos = i * 25

            # 🚇 터널 탐지
            if eleve < -10:
                if tunnel_start is None:
                    tunnel_start = pos
            else:
                if tunnel_start is not None and pos - tunnel_start >= 200:
                    self.structures.append(Tunnel(f'Tunnel_{len(self.structures)}','터널', tunnel_start, pos))
                tunnel_start = None

            # 🌉 교량 탐지
            if eleve > 15:
                if bridge_start is None:
                    bridge_start = pos
            else:
                if bridge_start is not None and pos - bridge_start >= 100:
                    self.structures.append(Bridge(f'Bridge_{len(self.structures)}','교량', bridge_start, pos))
                bridge_start = None


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

# 기본 구문 생성
base_txt = create_base_txt()

# 평면 및 종단선형 갯수 설정
count_horizon_alignment = estimate_alignment_count(MAX_TRACK_POSITION) #평면선형은 기본값 1000
count_vertical_alignment = estimate_alignment_count(MAX_TRACK_POSITION, 1500) #구배만 1500간격

# 평면선형 생성
base_txt += '\n,;평면선형\n'
base_txt += '\n'.join(AlignmentGenerator.create_horizontal_alignment(count_horizon_alignment))
base_txt += '\n'

# 종단선형 생성
base_txt += '\n,;종단선형\n'
base_txt += '\n'.join(AlignmentGenerator.create_vertical_alignment(count_vertical_alignment))
base_txt += '\n'

#지형 생성
elevation, nori , elevation_list = TerrainGerator.create_terrain()
base_txt += '\n,;표고\n'
base_txt += '\n'.join(elevation)
base_txt += '\n'

base_txt += '\n,;사면\n'
base_txt += ''.join(f"{a},{b}\n" for a, b in nori)
base_txt += '\n'

#구조물
structuregenerator = StructureGenerator()
structuregenerator.define_structure(elevation_list)
out = structuregenerator.create_structuesystax()

base_txt += '\n,;구조물\n'
base_txt += '\n'.join(out)
base_txt += '\n'

#종점
base_txt += '\n노선 종점\n'
base_txt += f'{MAX_TRACK_POSITION},.sta END STATION;\n'
base_txt += f'{MAX_TRACK_POSITION + 100},.stop 0;'

# 최종 출력
print('최종출력본')
print(base_txt)

# 저장
filepath = r'D:\BVE\루트\Railway\Route\연습용루트\테스트.csv'
try:
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in base_txt.splitlines():
            f.write(line + '\n')
    print(f"저장 완료: {filepath}")

except IOError as ex:
    print(f"파일 저장 중 오류 발생: {ex}")
