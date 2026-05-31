import random
import copy
import math
import csv
import matplotlib.pyplot as plt
import time

# csv 파일에서 지반고 정보와 측점 정보를 불러와서 gl 배열에 저장
def load_gl():
    gl = []
    fl = []
    cutfill = []
    with open('C:\\Users\\Administrator\\Documents\\gl.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # 첫 번째 행 건너뛰기
        for row in reader:
            station = int(row[1]) # 측점 정보 20의 배수로 반환
            ground_elevation = float(row[4])  # 지반고 정보
            design_elevation = float(row[5]) #계획고
            cutfill_d = float(row[6]) #절성고
            
            gl.append([station, ground_elevation])
            fl.append([station, design_elevation])
            cutfill.append([station, cutfill_d])
            
    return gl,fl, cutfill

#구조물판별
def cal_first_profile_structure(cutfill):
    structure = []

    for station, cutfill_d in cutfill:
        if cutfill_d  >= 12:
             structure.append([station , "터널"])
            
        elif cutfill_d  <= -12:
            structure.append([station , "교량"])
        else:
             structure.append([station , "토공"])

    return structure

# 공사비용 계산 함수
def cal_first_profile_money(structure):
    length_bridge = 0
    length_tunnel = 0
    length_excavation = 0

    for station, structure_type in structure:
        if "교량" in structure_type:
            length_bridge += station_unit
        if "터널" in structure_type:
            length_tunnel += station_unit
        if "토공" in structure_type:
            length_excavation += station_unit

    cost_bridge = (length_bridge / 1000) * 24574
    cost_tunnel = (length_tunnel / 1000) * 15784
    cost_excavation = (length_excavation / 1000) * 8620

    total_cost = cost_bridge + cost_tunnel + cost_excavation

    return total_cost

def generate_random_profile(start_elevation, end_elevation, start_station, end_station, num_points, min_distance, min_slope, max_slope, gl):
    points = [[start_station, start_elevation + 10]]

    current_station = start_station
    current_elevation = start_elevation + 10

    for _ in range(num_points - 1):

        distance_to_next = station_unit * math.ceil(random.uniform(min_distance,min_distance * 2) / station_unit)

        if current_station + distance_to_next >= end_station:
            distance_to_next = end_station - current_station

        next_station = current_station + distance_to_next
        if next_station >= end_station:
            break
        # Get ground elevation (gl) for current station
        current_gl = None
        for point in gl:
            if point[0] == next_station:  # 수정: 현재 측정 지점의 지반고로 업데이트
                current_gl = point[1]
                break

        if current_gl is None:
            raise ValueError(f"No ground elevation data found for station {next_station}")

        next_elevation = current_gl + 10

        current_station += distance_to_next
        current_elevation = next_elevation

        points.append([current_station, current_elevation])

    points[-1][0] = end_station
    points[-1][1] = end_elevation + 10

    return points



'배열을 다시 검사하여 이전 점과 비교' \
    '비교하여 이전점 표고가 현재 표고보다 10 이상 차이나면 현재 표고를 이전 표고 +-10으로 변경'
def check_and_adjust_elevation(points):
    adjusted_points = []

    for point in points:
        elevation = point[1]  # 현재 점의 표고

        if elevation < 300:
            adjusted_points.append(point)

    return adjusted_points
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

        if distance ==0 or height == 0:
        # 거리가 0인 경우, 적절한 처리를 수행하거나 오류를 방지하기 위한 조치를 취한다.
            slope = 0  # 예시로 0으로 설정
            #print("계획고  생성중 에러발생! " , "높이" , height , "거리" ,distance ,"종점", end_station,"시점", start_station)
        else:
            slope = height / distance * 1000

        num_steps = int(distance / station_unit)  # 20의 배수인 측점 개수 계산

        for j in range(num_steps + 1):
            current_station = start_station + j * station_unit
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


# 공사비용 계산 함수
def cal_profile_money(new_structure):
    length_bridge = 0
    length_tunnel = 0
    length_excavation = 0

    for station, structure_type in new_structure:
        if "교량" in structure_type:
            length_bridge += station_unit
        if "터널" in structure_type:
            length_tunnel += station_unit
        if "토공" in structure_type:
            length_excavation += station_unit

    cost_bridge = (length_bridge / 1000) * 24574
    cost_tunnel = (length_tunnel / 1000) * 15784
    cost_excavation = (length_excavation / 1000) * 8620

    new_total_cost = cost_bridge + cost_tunnel + cost_excavation

    return new_total_cost

#노선 유효성 체크
def fitness(points,total_cost,new_total_cost):
    score = 0  # Initial score is 0

    for i in range(len(points) - 1):
        start_station = points[i][0]
        start_elevation = points[i][1]
        end_station = points[i + 1][0]
        end_elevation = points[i + 1][1]

        # 변수설정
        height = end_elevation - start_elevation
        distance = end_station - start_station

        if distance ==0 or height == 0:
        # 거리가 0인 경우, 적절한 처리를 수행하거나 오류를 방지하기 위한 조치를 취한다.
            slope = 0  # 예시로 0으로 설정
            #print("유효성 체크중 발생! " , "높이" , height , "거리" ,distance ,"종점", end_station,"시점", start_station)
        else:
            slope = height / distance * 1000

        #최소구배길이 미달시 0점
        if distance <= 200:
            return score
        
    
        len_score = 1
        score += len_score

        #구배점수 계산
        slope_score = 1
        if -25 <= slope <= 25:
            score += slope_score
        else:
            score = 0
    # 두 종단간 공사비 비교
    cost_score = 2
    if score == 0:
        return score
    else:

        if total_cost >= new_total_cost:
            score += cost_score
        else:
             score -= 2
    max_score = (len(points) - 1) * (len_score + slope_score) + cost_score       
    normalized_score = (score / max_score) * 100  # 백점 만점으로 변환
    # Return the score
    return normalized_score

#메인코드
#변수들

min_distance = 2000  # 측점간 최소 거리
min_slope = -0.025  # 최소 경사
max_slope = 0.025  # 최대 경사
num_points = 60  # 측점 생성 갯수
station_unit = int(input("측점 간격을 입력하세요:    "))  #측점 간격 20,40
gl, fl, cutfill = load_gl()
structure = cal_first_profile_structure(cutfill)
total_cost = cal_first_profile_money(structure) #총공사비
start_elevation = gl[0][1]
end_elevation = gl[-1][1]
start_station = gl[0][0]
end_station = gl[-1][0]
# 랜덤 프로파일 생성


points = generate_random_profile(start_elevation, end_elevation, start_station, end_station, num_points, min_distance, min_slope, max_slope, gl)
points2 = copy.deepcopy(points)
points2 = check_and_adjust_elevation(points2)








station_elv = generate_station_elv(points)
new_cutfill = calculate_cutfill(station_elv, gl)
new_structure = cal_profile_structure(new_cutfill)
new_total_cost = cal_profile_money(new_structure)#신규노선 공사비

station_elv2 = generate_station_elv(points2)
new_cutfill2 = calculate_cutfill(station_elv2, gl)
new_structure2 = cal_profile_structure(new_cutfill2)
new_total_cost2 = cal_profile_money(new_structure2)#신규노선 공사비
'''
print("초기공사비", total_cost , "백만원")
print("새 공사비", new_total_cost, "백만원")
print("조정된 노선 공사비", new_total_cost2, "백만원")
print("차액 ", new_total_cost - total_cost, "백만원")
print(" 새 차액 ", new_total_cost2 - total_cost, "백만원")
print("점수 ", fitness(points,total_cost,new_total_cost))
print(" 새 점수 ", fitness(points2,total_cost,new_total_cost2))
'''




#루프 시작
best_points = points  # 초기 점수가 가장 높은 점들로 시작
best_score = fitness(points, total_cost, new_total_cost)  # 초기 점수 계산

i=0
start_time = time.time()
while True:
    # 랜덤 프로파일 생성
    points = generate_random_profile(start_elevation, end_elevation, start_station, end_station, num_points, min_distance, min_slope, max_slope, gl)
    points2 = copy.deepcopy(points)
    points2 = check_and_adjust_elevation(points2)

    station_elv = generate_station_elv(points)
    new_cutfill = calculate_cutfill(station_elv, gl)
    new_structure = cal_profile_structure(new_cutfill)
    new_total_cost = cal_profile_money(new_structure)  # 신규노선 공사비

    station_elv2 = generate_station_elv(points2)
    new_cutfill2 = calculate_cutfill(station_elv2, gl)
    new_structure2 = cal_profile_structure(new_cutfill2)
    new_total_cost2 = cal_profile_money(new_structure2)  # 신규노선 공사비

    # 새로운 점수 계산
    new_score = fitness(points2, total_cost, new_total_cost2)

    # 최적의 점수인 경우 결과 업데이트
    if new_score > best_score:
        best_points = points2
        best_score = new_score

        # 현재 회차 점수와 탈락 여부 출력
    print("회차:", i + 1)
    print("현재 회차 점수:", new_score)
    if new_score > 55:
        print("탈락 여부: 통과")
    else:
        print("탈락 여부: 탈락")

    i += 1  # 현재 회차 변수 증가

    # 종료 조건 확인
    if best_score > 55:
        break
end_time = time.time()
elapsed_time = end_time - start_time
# 최적의 결과 출력
print("종료회차:", i)
print("루프 소요 시간:", elapsed_time, "초")
print("최적의 점수:", best_score)
print("최적의 점들:", best_points)
print("최적의 공사비:", new_total_cost2)
print("차액:", new_total_cost2-total_cost)
# 경사도 계산
slopes = []
for i in range(1, len(points)):
    distance = points[i][0] - points[i-1][0]
    elevation_change = points[i][1] - points[i-1][1]
    if distance != 0:
        slope = elevation_change / distance
    else:
        slope = 0  # 거리가 0인 경우 경사도를 0으로 처리
    slopes.append(slope)




#아래는 시각화 코드
# 그래프 그리기
gl_stations = [point[0] for point in gl]
gl_elevations = [point[1] for point in gl]
fl_stations = [point[0] for point in points]
fl_elevations = [point[1] for point in points]

fl_stations2 = [point[0] for point in best_points]
fl_elevations2 = [point[1] for point in best_points]


plt.plot(gl_stations, gl_elevations,linestyle='--', color='g', label='GL')
plt.legend()
plt.plot(fl_stations, fl_elevations, linestyle='-', marker='x',color='r', label='new_fl')
plt.legend()
plt.plot(fl_stations2, fl_elevations2, linestyle=':', marker='o',color='b', label='best_points')
plt.legend()
plt.xlabel('station')
plt.ylabel('elevation')
plt.title('graph')
plt.grid(True)

'''표고표시'''
for i in range(len(points)):
    station = points[i][0]
    elevation = points[i][1]
    plt.text(station, elevation, f'{elevation:.2f}', ha='center', va='bottom',color='r')
'''경사도
텍스트
추가'''
for i in range(1, len(points)):
    x1 = points[i-1][0]
    y1 = fl_elevations[i-1]
    x2 = points[i][0]
    y2 = fl_elevations[i]
    slope = slopes[i-1] * 1000
    text_x = (x1 + x2) / 2
    text_y = (y1 + y2) / 2
    text = f"{slope:.3f}‰"
    plt.text(text_x, text_y, text, ha='center',color='r')


# 새노선 경사도 계산
slopes2 = []
for i in range(1, len(best_points)):
    distance = best_points[i][0] - best_points[i-1][0]
    elevation_change = best_points[i][1] - best_points[i-1][1]
    if distance != 0:
        slope = elevation_change / distance
    else:
        slope = 0  # 거리가 0인 경우 경사도를 0으로 처리
    slopes2.append(slope)


'''조정노선 경사도
텍스트
추가'''
for i in range(1, len(best_points)):
    x1 = best_points[i-1][0]
    y1 = fl_elevations2[i-1]
    x2 = best_points[i][0]
    y2 = fl_elevations2[i]
    slope = slopes2[i-1] * 1000
    text_x = (x1 + x2) / 2
    text_y = (y1 + y2) / 2
    text = f"{slope:.3f}‰"
    plt.text(text_x, text_y, text, ha='center',color='b')












# Plot distance between points
for i in range(len(points) - 1):
    x1 = points[i][0]
    y1 = points[i][1]
    x2 = points[i + 1][0]
    y2 = points[i + 1][1]
    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    mid_x = (x1 + x2) / 2
    mid_y = 75
    plt.text(mid_x, mid_y, f'{distance:.2f}', ha='center', va='center',color='r')


#조정노선
# Plot distance between points
for i in range(len(best_points) - 1):
    x1 = best_points[i][0]
    y1 = best_points[i][1]
    x2 = best_points[i + 1][0]
    y2 = best_points[i + 1][1]
    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    mid_x = (x1 + x2) / 2
    mid_y = 50
    plt.text(mid_x, mid_y, f'{distance:.2f}', ha='center', va='center',color='b')



# 그래프 표시






plt.show()
