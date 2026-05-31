import os
import csv
import re

os.chdir("C:\\TEMP\\")

# 파일 변수 선언
bridge_file = "bridge.csv"
tunnel_file = "tunnel.csv"
curve_file = "curve.csv"
pitch_file = "pitch.csv"
object_file = "object.txt"
distance_out_file = "km_post.txt"
curve_out_file = "curve_post.txt"
pitch_out_file = "pitch_post.txt"

# 곡선 클래스 생성.
class CurveGroup:
    def __init__(self, name, radius):
        self.name = name
        self.radius = radius
        self.stations = []

    def add_station(self, station, name):
        self.stations.append((station, name))

# 구배 클래스 생성.
class GradeGroup:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade
        self.stations = []

    def add_station(self, station, name):
        self.stations.append((station, name))


#곡선반경이 100의 배수가 아닌경우 이를 변경하는 함수
def round_to_nearest_100(num):
    quotient, remainder = divmod(num, 100)
    rounded_quotient = round(quotient)
    rounded_num = rounded_quotient * 100
    if remainder == 50:
        rounded_num += 50
    elif remainder > 50:
        rounded_num += 100
    return rounded_num

# 일반철도용 곡선표 인덱스 얻기
def get_highsppedrail_curve_object_index():
    curve_group = extract_curve_groups()
    highsppedrail_curve_object_index = []
    structure_types = determine_structure_types_for_curve(curve_group)
    with open(object_file, 'r', encoding='utf8') as f:

        for cg in curve_group:
            radius = cg.radius
            match_found = False
            f.seek(0)
            # 반지름이 100의 배수인지 체크
            if radius % 100 != 0:
                radius = round_to_nearest_100(radius)

            for line in f:
                if "철도표준도\\궤도\\선로제표\\고속철도\\곡선표\\" in line and any(st in line for st in structure_types) and str(radius) in line:
                    re.search(r'\d{}\d\.csv'.format(radius), line)
                    object_index = re.search(r'\d+', line).group(0)
                    highsppedrail_curve_object_index.append(object_index)
                    match_found = True
                    break
                else:
                    continue
    return highsppedrail_curve_object_index

# 일반철도용 곡선표 인덱스 얻기
def get_curve_object_index():
    curve_group = extract_curve_groups()
    curve_object_index = []
    structure_types = determine_structure_types_for_curve(curve_group)
    with open(object_file, 'r', encoding='utf8') as f:

        for cg in curve_group:
            radius = cg.radius
            match_found = False
            f.seek(0)
            # 반지름이 100의 배수인지 체크
            if radius % 100 != 0:
                radius = round_to_nearest_100(radius)

            for line in f:
                if "철도표준도\\궤도\\선로제표\\일반철도\\곡선표\\" in line and any(st in line for st in structure_types) and str(radius) in line:
                    re.search(r'\d{}\d\.csv'.format(radius), line)
                    object_index = re.search(r'\d+', line).group(0)
                    curve_object_index.append(object_index)
                    match_found = True
                    break
                else:
                    continue
    return curve_object_index

# 일반철도용 구배표 인덱스 얻기
def get_grade_object_index():
    grade_group = extract_grade_groups()
    grade_object_index = []
    structure_types = determine_structure_types_for_grade(grade_group)
    with open(object_file, 'r', encoding='utf8') as f:

        for gg in grade_group:
            grade = gg.grade
            match_found = False
            f.seek(0)

            #상구배 하구배 체크
            # 구배가 0인 경우 LEVEL로 변경
            if grade > 0:
                grade = '상' + str(round((grade)))
            elif grade == 0:
                grade = 'L'
            elif grade < 0:
                grade = '하' + str(abs(round((grade))))

            for line in f:
                #토공용
                if  '토공용'in structure_types:
                    if "철도표준도\\궤도\\선로제표\\일반철도\\구배표\\" in line and str(grade) in line:
                        re.search(r'\d{}\d\.csv'.format(grade), line)
                        object_index = re.search(r'\d+', line).group(0)
                        grade_object_index.append(object_index)
                        match_found = True
                        break

                    else:
                        continue
                #교량용
                elif '교량용'in structure_types:
                    if "철도표준도\\궤도\\선로제표\\일반철도\\구배표\\교량용\\" in line and str(grade) in line:
                        re.search(r'\d{}\d\.csv'.format(grade), line)
                        object_index = re.search(r'\d+', line).group(0)
                        grade_object_index.append(object_index)
                        match_found = True
                        break
    
                    else:
                        continue

                #터널용
                elif '터널용'in structure_types:
                    if "철도표준도\\궤도\\선로제표\\도시철도\\구배표\\" in line and str(grade) in line:
                        re.search(r'\d{}\d\.csv'.format(grade), line)
                        object_index = re.search(r'\d+', line).group(0)
                        grade_object_index.append(object_index)
                        match_found = True
                        break

                    else:
                        continue

    return grade_object_index

# 교량 시종점 추출
def determine_bridge_range():
    with open(bridge_file, newline='', encoding='utf8') as f:
        reader = csv.reader(f)
        # Skip the header row
        next(reader)
        # Read the remaining rows to get the bridge ranges
        bridge_ranges = []
        for row in reader:
            bridge_range = [int(row[0]), int(row[1])]
            bridge_ranges.append(bridge_range)
        return bridge_ranges


# 터널 시종점 추출
def determine_tunnel_range():
    with open(tunnel_file, newline='', encoding='utf8') as f:
        reader = csv.reader(f)
        # Skip the header row
        next(reader)
        # Read the remaining rows to get the tunnel ranges
        tunnel_ranges = []
        for row in reader:
            tunnel_range = [int(row[0]), int(row[1])]
            tunnel_ranges.append(tunnel_range)
        return tunnel_ranges


# 구조물 판단 함수(거리표용)
def determine_structure_types(station_list):
    # Extract the bridge and tunnel ranges from the CSV files
    bridge_ranges = determine_bridge_range()
    tunnel_ranges = determine_tunnel_range()

    # Initialize a list to hold the structure types for each station
    structure_types = []

    # Iterate over the stations in the input list
    for station in station_list:
        # Check if the station falls inside a bridge range
        is_bridge = False
        for bridge_range in bridge_ranges:
            if bridge_range[0] <= station <= bridge_range[1]:
                structure_types.append('교량용')
                is_bridge = True
                break
        if is_bridge:
            continue
        # Check if the station falls inside a tunnel range
        is_tunnel = False
        for tunnel_range in tunnel_ranges:
            if tunnel_range[0] <= station <= tunnel_range[1]:
                structure_types.append('터널용')
                is_tunnel = True
                break
        if is_tunnel:
            continue
        # If the station does not fall inside a bridge or tunnel range, add "earthworks"
        structure_types.append('토공용')

    # Return the list of structure types
    return structure_types


# 구조물 판단 함수(곡선표용)
def determine_structure_types_for_curve(curve_group):
    
    # Extract the bridge and tunnel ranges from the CSV files
    bridge_ranges = determine_bridge_range()
    tunnel_ranges = determine_tunnel_range()

    # Initialize a list to hold the structure types for each station
    structure_types = []
    curve_group = extract_curve_groups()
    # Iterate over the stations in the input curve group
    for curve_group in curve_group:
        for station, _ in curve_group.stations:

            # Check if the station falls inside a bridge range
            is_bridge = False
            for bridge_range in bridge_ranges:
                if bridge_range[0] <= round(station) <= bridge_range[1]:
                    structure_types.append('교량용')
                    is_bridge = True
                    break
            if is_bridge:
                continue
            # Check if the station falls inside a tunnel range
            is_tunnel = False
            for tunnel_range in tunnel_ranges:
                if tunnel_range[0] <= round(station) <= tunnel_range[1]:
                    structure_types.append('터널용')
                    is_tunnel = True
                    break
            if is_tunnel:
                continue
            # If the station does not fall inside a bridge or tunnel range, add "earthworks"
            structure_types.append('토공용')

    # Return the list of structure types

    return structure_types

# 구조물 판단 함수(구배표용)
def determine_structure_types_for_grade(grade_group):
    
    # Extract the bridge and tunnel ranges from the CSV files
    bridge_ranges = determine_bridge_range()
    tunnel_ranges = determine_tunnel_range()

    # Initialize a list to hold the structure types for each station
    structure_types = []
    grade_group = extract_grade_groups()
    # Iterate over the stations in the input curve group
    for grade_group in grade_group:
        for station, _ in grade_group.stations:

            # Check if the station falls inside a bridge range
            is_bridge = False
            for bridge_range in bridge_ranges:
                if bridge_range[0] <= round(station) <= bridge_range[1]:
                    structure_types.append('교량용')
                    is_bridge = True
                    break
            if is_bridge:
                continue
            # Check if the station falls inside a tunnel range
            is_tunnel = False
            for tunnel_range in tunnel_ranges:
                if tunnel_range[0] <= round(station) <= tunnel_range[1]:
                    structure_types.append('터널용')
                    is_tunnel = True
                    break
            if is_tunnel:
                continue
            # If the station does not fall inside a bridge or tunnel range, add "earthworks"
            structure_types.append('토공용')

    # Return the list of structure types

    return structure_types

# km표지인지 m표인지 판단함수
def determine_km_table(station_list):
    km_table = []
    for station in station_list:
        if station % 1000 == 0:
            km_table.append('km표')
        elif station % 200 == 0 and station % 1000 != 0:
            km_table.append('m표')
        else:
            km_table.append('null')
    return km_table


# 거리표 오브젝트 인덱스 얻기
def get_object_index(station_list):
    # 변수 설정
    km_table = determine_km_table(station_list)
    structure_types = determine_structure_types(station_list)
    a = [index // 1000 for index in station_list]
    object_indices = []
    km_file_names = []
    m_file_names = []

    # .csv파일 이름 리스트 셍성
    for i, station in enumerate(station_list):
        if station % 1000 == 0:
            km_file_names.append(f"{km_table[i]}\{structure_types[i]}\{a[i]}.csv")
        elif station % 200 == 0 and station % 1000 != 0:
            km_file_names.append(f"{km_table[i]}\{structure_types[i]}\{station_list[i]}.csv")

    with open(object_file, 'r', encoding='utf8') as f:
        for i, km_file_name in enumerate(km_file_names):
            match_found = False
            f.seek(0)
            for line in f:
                if km_file_name in line:
                    object_index = int(line.split('(')[-1].split(')')[0])
                    object_indices.append(object_index)
                    match_found = True
                    break
                elif km_file_name in line and "km표" in line:
                    continue
            if not match_found and station_list[i] % 1000 != 0 and station_list[i] % 200 == 0:
                # If a match is not found and the station number is a multiple of 200 but not a multiple of 1000,
                # search for the object index in the line without 'km표'
                f.seek(0)
                for line in f:
                    if km_file_name in line and "km표" not in line:
                        object_index = int(line.split('(')[-1].split(')')[0])
                        object_indices.append(object_index)
                        match_found = True
                        break
            if not match_found:
                object_indices.append(None)

    return object_indices


# 곡선 그룹 추출
def extract_curve_groups():
    with open('curve.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)
        curve_info = list(reader)
    curve_groups = []
    current_curve_group = None
    group_counter = 0
    for info in curve_info:
        name = info[0]
        station = float(info[1])
        radius = int(info[2])

        if name == 'BC' or name == 'SP':
            if current_curve_group is not None:
                curve_groups.append(current_curve_group)
            group_counter += 1
            current_curve_group = CurveGroup(name=f"Curve Group: {group_counter}", radius=radius)
            current_curve_group.add_station(station, name)

        elif name == 'EC' or name == 'PS':
            if current_curve_group is not None:
                current_curve_group.add_station(station, name)
                curve_groups.append(current_curve_group)
                current_curve_group = None

        elif name == 'PC' or name == 'CP':
            current_curve_group.add_station(station, name)

    if current_curve_group is not None:
        curve_groups.append(current_curve_group)

    return curve_groups

# 구배 그룹 추출
def extract_grade_groups():
    with open(pitch_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        grade_info = list(reader)
        grade_groups = []
        current_grade_group = None
        prev_line = None
        group_counter = 0

    for i, info in enumerate(grade_info):
        name = info[0]
        station = float(info[1])
        grade = float(info[2])
        
        # 이전 줄과 다음 줄 찾기
        prev_line = grade_info[i-1] if i > 0 else None
        next_line = grade_info[i+1] if i < len(grade_info)-1 else None

        if name == 'BVC':
            if current_grade_group is not None:
                grade_groups.append(current_grade_group)
            group_counter += 1
            current_grade_group = GradeGroup(name=f"Grade Group: {group_counter}", grade=grade)
            current_grade_group.add_station(station, name)

        elif name == 'EVC':
            if current_grade_group is not None:
                current_grade_group.add_station(station, name)
                grade_groups.append(current_grade_group)
                current_grade_group = None

        elif name == 'VIP':
            # 종곡선이 존재하는경우
            if current_grade_group is not None and prev_line[0] == 'BVC' and next_line[0] == 'EVC':
                current_grade_group.add_station(station, name)

            # 종곡선이 존재하지 않는경우
            elif current_grade_group is not None and prev_line[0] == 'EVC' and next_line[0] == 'BVC':
                if current_grade_group is not None:
                    grade_groups.append(current_grade_group)
                    group_counter += 1
                    current_grade_group = GradeGroup(name=f"Grade Group: {group_counter}", grade=grade)
                    current_grade_group.add_station(station, name)

    if current_grade_group is not None:
        grade_groups.append(current_grade_group)

    return grade_groups


#메인함수
def main():
    # 거리표 추출
    # Get the list of stations
    station_list = []
    input_station = int(input("Press input station: "))
    for i in range(0, input_station + 1, 200):
        station_list.append(i)

    # Get the object indices for each station
    object_indices = get_object_index(station_list)

    # Combine station_list, object_indices, and ".freeobj 0;" into a string
    result_str = ""
    for i in range(len(station_list)):
        result_str += str(station_list[i]) + ",.freeobj 0;" + str(object_indices[i]) + ";\n"

    # Save the result to a file
    with open(distance_out_file, "w", encoding="utf8") as f:
        f.write(result_str)

    # 곡선표 추출
    curve_object_index = get_curve_object_index()
    curve_groups = extract_curve_groups()

    result_str = ""

    for group, index in zip(curve_groups, curve_object_index):
        for station, name in group.stations:
            result_str += f"{station},.freeobj 0;{index};\n"


    # Save the result to a file
    with open(curve_out_file, "w", encoding="utf8") as f:
        f.write(result_str)

    # 구배표 추출
    grade_object_index = get_grade_object_index()
    grade_groups = extract_grade_groups()

    result_str = ""

    for group, index in zip(grade_groups, grade_object_index):
        for station, name in group.stations:
            result_str += f"{station},.freeobj 0;{index};\n"


    # Save the result to a file
    with open(pitch_out_file, "w", encoding="utf8") as f:
        f.write(result_str)

if __name__=='__main__':
    main()
