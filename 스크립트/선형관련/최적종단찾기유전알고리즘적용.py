import random
import math
import csv
import matplotlib.pyplot as plt
import openpyxl
from tkinter import filedialog
import openpyxl

# 전역변수
chain = 25
isstartend = True

# 실시설계
detail_design = [(0, 170.795), (4660, 223.66), (11825, 255.848)]

# 초기 해집단 생성
def generate_initial_population(gl, pop_size, num_points, min_distance):
    population = []
    for _ in range(pop_size):
        individual = generate_random_profile(num_points, min_distance, gl)
        individual = check_and_adjust_elevation(individual)

        alternative['종단'] = individual
        alternative['최급기울기'] = find_steepest_gradient(individual)
        alternative['계획고'] = generate_station_elv(individual)
        alternative['절성고'] = calculate_cutfill(alternative['계획고'], gl)
        alternative['구조물'] = cal_profile_structure(alternative['절성고'])
        alternative['구조물위치'] = find_structure_ranges(alternative['구조물'])
        alternative['구조물갯수'] = count_structures(alternative['구조물위치'])
        alternative['공사비'] = cal_profile_money(alternative['구조물'])
        alternative['점수'] = fitness(individual)
        
        population.append(alternative)
    return population

# 적합도 함수 (목표 함수)
def fitness(individual):
    score = 0
    profile = individual['종단']
    for i in range(len(profile) - 1):
        start_station = profile[i][0]
        start_elevation = profile[i][1]
        end_station = profile[i + 1][0]
        end_elevation = profile[i + 1][1]

        height = end_elevation - start_elevation
        distance = end_station - start_station

        if distance == 0:
            slope = 0
        else:
            slope = height / distance * 1000

        if distance <= 200:
            score = 0

        slope_score = 10
        if slope <= 25:
            score += slope_score
        else:
            score = 0

    return score


# 선택 연산자
def selection(population, fitness_scores):
    selected = random.choices(population, weights=fitness_scores, k=len(population))
    return selected

# 교차 연산자
def crossover(parent1, parent2):
    crossover_point = random.randint(1, len(parent1) - 2)
    child1 = parent1[:crossover_point] + parent2[crossover_point:]
    child2 = parent2[:crossover_point] + parent1[crossover_point:]
    return child1, child2

# 돌연변이 연산자
def mutation(individual, mutation_rate, gl):
    if random.random() < mutation_rate:
        mutate_point = random.randint(1, len(individual) - 2)
        gl_station, gl_elevation = gl[mutate_point]
        individual[mutate_point][1] = gl_elevation + random.uniform(-20, 20)
    return individual

# 유전 알고리즘
def genetic_algorithm(gl, pop_size, num_points, min_distance, generations, mutation_rate):
    population = generate_initial_population(gl, pop_size, num_points, min_distance)
    
    for generation in range(generations):
        fitness_scores = [fitness(individual) for individual in population]
        
        if max(fitness_scores) == 0:
            continue

        population = selection(population, fitness_scores)
        next_generation = []

        for i in range(0, len(population), 2):
            parent1 = population[i]
            parent2 = population[i + 1] if i + 1 < len(population) else population[0]
            child1, child2 = crossover(parent1, parent2)
            next_generation.extend([child1, child2])

        population = [mutation(individual, mutation_rate, gl) for individual in next_generation]
        best_individual = population[fitness_scores.index(max(fitness_scores))]
        print(f'Generation {generation + 1}: Best Fitness = {max(fitness_scores)}')

    best_individual = population[fitness_scores.index(max(fitness_scores))]
    return best_individual

# 주요 함수 정의 (파일 로드, 랜덤 프로파일 생성 등)
def load_gl():
    gl = []
    file_path = filedialog.askopenfilename(title="파일 선택", filetypes=[("텍스트 파일", "*.txt")])
    if file_path:
        try:
            with open(file_path, 'r', encoding='UTF-8') as file:
                reader = csv.reader(file)
                next(reader)
                for row in reader:
                    station = int(row[0])
                    ground_elevation = float(row[1])
                    gl.append([station, ground_elevation])
        except FileNotFoundError:
            print("파일을 찾을 수 없습니다.")
        except Exception as e:
            print("파일을 읽는 중 오류가 발생했습니다:", e)
    else:
        print("파일 선택이 취소되었습니다.")
    return gl

def generate_random_profile(num_points, min_distance, gl):
    start_station, start_elevation = gl[0]
    end_station, end_elevation = gl[-1]

    detail_start_station, detail_start_elevation = detail_design[0]
    detail_end_station, detail_end_elevation = detail_design[-1]

    points = [[detail_start_station, detail_start_elevation]] if isstartend else [[start_station, start_elevation + 10]]
    current_station = start_station
    current_elevation = start_elevation + 10

    for _ in range(num_points - 1):
        distance_to_next = chain * math.ceil(random.uniform(min_distance, min_distance * 2) / chain)
        if current_station + distance_to_next >= end_station:
            break

        next_station = current_station + distance_to_next
        next_elevation = None
        for station, elevation in gl:
            if station == next_station:
                next_elevation = elevation + 10
                break

        if next_elevation is None:
            raise ValueError(f"No ground elevation data found for station {next_station}")

        current_station = next_station
        current_elevation = next_elevation
        points.append([current_station, current_elevation])

    points.append([detail_end_station, detail_end_elevation]) if isstartend else points.append([end_station, end_elevation + 10])
    return points

def check_and_adjust_elevation(profile):
    adjusted_profile = []
    for i, (station, elevation) in enumerate(profile):
        rand_el = random.uniform(0, 20)
        if i > 0:
            prev_station, prev_elevation = adjusted_profile[-1]
            if abs(elevation - prev_elevation) > 20:
                elevation = prev_elevation + (rand_el if elevation > prev_elevation else -rand_el)
        adjusted_profile.append([station, elevation])
    return adjusted_profile

#최급기울기 찾기
def find_steepest_gradient(g):
    max_gradient = 0
    steepest_gradient_station = None
    
    for i in range(len(g) - 1):
        station1, elevation1 = g[i]
        station2, elevation2 = g[i + 1]
        
        # 두 점 사이의 거리
        distance = station2 - station1
        
        if distance == 0:
            continue
        
        # 기울기 계산
        gradient = abs((elevation2 - elevation1) / distance) * 1000
        
        # 최대 기울기 갱신
        if gradient > max_gradient:
            max_gradient = gradient
            steepest_gradient_station = station1 if elevation1 < elevation2 else station2
            
    return max_gradient, len(g) - 2

#표고점을 20간격으로 계획고 생성
def generate_station_elv(points):
    station_elv = []

    for i in range(len(points) - 1):
        start_station = points[i][0]
        start_elevation = points[i][1]
        end_station = points[i + 1][0]
        end_elevation = points[i + 1][1]

        
        height = end_elevation - start_elevation
        distance = end_station - start_station

    
        if distance == 0:
            slope = 0
        else:
            slope = height / distance * 1000

        num_steps = int(distance / chain)  # 20의 배수인 측점 개수 계산

        for j in range(num_steps + 1):
            current_station = start_station + j * chain
            current_elevation = start_elevation + slope/1000 * (current_station - start_station)
            station_elv.append([current_station, current_elevation])

    return station_elv

#절토성토고 계산
def calculate_cutfill(station_elv, gl):
    new_cutfill = []
    
    for gl_station, el in gl:  # 지반고 추출
        for elv_station, dl in station_elv:  # 계획고 추출
            if gl_station == elv_station:
                height_d = el - dl
                new_cutfill.append([gl_station, height_d])

    return new_cutfill

#구조물판별
def cal_profile_structure(new_cutfill):
    new_structure = []

    for station, cutfill_d in new_cutfill:
        if cutfill_d  >= 12:
             new_structure.append([station , "터널"])
            
        elif cutfill_d  <= -12:
            new_structure.append([station , "교량"])
        else:
             new_structure.append([station , "토공"])

    return new_structure

#구조물 측점
def find_structure_ranges(structure_list):
    ranges = {}
    bridge_count = 1
    tunnel_count = 1

    current_structure = None
    start_station = None

    for i, (station, structure) in enumerate(structure_list):
        if structure == '교량':
            if current_structure != '교량':
                if current_structure is not None:
                    if current_structure == '터널':
                        key = f'T{tunnel_count}'
                        ranges[key] = (start_station, structure_list[i - 1][0])
                        tunnel_count += 1
                start_station = station
                current_structure = '교량'
        elif structure == '터널':
            if current_structure != '터널':
                if current_structure is not None:
                    if current_structure == '교량':
                        key = f'B{bridge_count}'
                        ranges[key] = (start_station, structure_list[i - 1][0])
                        bridge_count += 1
                start_station = station
                current_structure = '터널'
        else:
            if current_structure == '교량':
                key = f'B{bridge_count}'
                ranges[key] = (start_station, structure_list[i - 1][0])
                bridge_count += 1
            elif current_structure == '터널':
                key = f'T{tunnel_count}'
                ranges[key] = (start_station, structure_list[i - 1][0])
                tunnel_count += 1
            current_structure = None
            start_station = None

    if current_structure == '교량':
        key = f'B{bridge_count}'
        ranges[key] = (start_station, structure_list[-1][0])
    elif current_structure == '터널':
        key = f'T{tunnel_count}'
        ranges[key] = (start_station, structure_list[-1][0])

    return ranges

# 구조물 갯수
def count_structures(structure_ranges):
    count_bridge = 0
    count_tunnel = 0

    for key in structure_ranges.keys():
        if key.startswith('B'):
            count_bridge += 1
        elif key.startswith('T'):
            count_tunnel += 1

    return count_bridge, count_tunnel

# 공사비용 계산 함수
def cal_profile_money(new_structure):
    length_bridge = 0
    length_tunnel = 0
    length_excavation = 0

    for station, structure_type in new_structure:
        if "교량" in structure_type:
            length_bridge += 20
        if "터널" in structure_type:
            length_tunnel += 20
        if "토공" in structure_type:
            length_excavation += 20

    cost_bridge = (length_bridge / 1000) * 24574
    cost_tunnel = (length_tunnel / 1000) * 15784
    cost_excavation = (length_excavation / 1000) * 8620

    new_total_cost = cost_bridge + cost_tunnel + cost_excavation

    return new_total_cost

def create_excel(final_alternative):
    # 엑셀 파일 생성
    wb = openpyxl.Workbook()

    # '종단' 시트 생성
    ws1 = wb.active
    ws1.title = "종단"

    # 데이터 쓰기
    # 헤더 추가
    ws1.append(["측점", "계획고"])
    for station, elevation in final_alternative['종단']:
        ws1.append([station, elevation])

    # '구조물' 시트 생성
    ws2 = wb.create_sheet(title="구조물")

    # 데이터 쓰기
    # 헤더 추가
    ws2.append(["구조물", "시점", "종점","길이"])
    
    for struct_type, (start_station, end_station) in final_alternative['구조물위치'].items():
        length = end_station - start_station
        ws2.append([struct_type, start_station, end_station,length])

    # 엑셀 파일 저장
    wb.save('c:\\temp\\최적대안.xlsx')
    
# 메인 실행
if __name__ == "__main__":
    gl = load_gl()
    pop_size = 50
    num_points = 10
    min_distance = 1000
    generations = 100
    mutation_rate = 0.1
    results = []
    alternative = {}
    
    #최대 vip갯수
    max_vip = int(gl[-1][0] / min_distance)
    print(max_vip)

    best_profile = genetic_algorithm(gl, pop_size, num_points, min_distance, generations, mutation_rate)
    print(f'Best Profile: {best_profile}')

    # 최적 종단을 그래프로 그리기
    stations, elevations = zip(*best_profile)
    glx, gly = zip(*gl)
    plt.plot(glx, gly, linestyle='-', color='k', label='GL')
    plt.plot(stations, elevations, marker='o', linestyle='-', color='red', label='Optimal Profile')
    flx, fly = zip(*detail_design)
    plt.plot(flx, fly, marker='o', linestyle='-', color='b', label='Detail Design')
    plt.xlabel('Station')
    plt.ylabel('Elevation')
    plt.title('Optimal Alignment')
    plt.legend()
    plt.show()
