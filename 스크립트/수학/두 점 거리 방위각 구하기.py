import math
from geopy.distance import geodesic


def calculate_distance(x1, y1, x2, y2):
    # Calculate the distance between two points in Cartesian coordinates
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    distance_x = abs(x2 - x1)
    distance_y = abs(y2 - y1)
    return distance, distance_x, distance_y


def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing


def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2


def calculate_distance_lat_lon(lat1, lon1, lat2, lon2):
    # Calculate the distance between two points in geographic coordinates (latitude and longitude)
    distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
    distance_lat = geodesic((lat1, lon1), (lat2, lon1)).kilometers
    distance_lon = geodesic((lat1, lon1), (lat1, lon2)).kilometers
    return distance,distance_lat,distance_lon


def calculate_bearing_lat_lon(lat1, lon1, lat2, lon2):
    # Calculate the bearing (direction) between two points in geographic coordinates (latitude and longitude)
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad

    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    bearing = math.atan2(y, x)

    bearing = math.degrees(bearing)
    if bearing < 0:
        bearing += 360

    return bearing


def calculate_destination_coordinates_lat_lon(lat1, lon1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in geographic coordinates
    radius = 6371  # Earth's radius in kilometers
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    angular_distance = distance / radius

    lat2_rad = math.asin(math.sin(lat1_rad) * math.cos(angular_distance) +
                         math.cos(lat1_rad) * math.sin(angular_distance) * math.cos(math.radians(bearing)))

    lon2_rad = lon1_rad + math.atan2(math.sin(math.radians(bearing)) * math.sin(angular_distance) * math.cos(lat1_rad),
                                     math.cos(angular_distance) - math.sin(lat1_rad) * math.sin(lat2_rad))

    lat2 = math.degrees(lat2_rad)
    lon2 = math.degrees(lon2_rad)

    return lat2, lon2


#메인

while 1:
    coordinate_system = int(input("입력 좌표 방식을 선택하세요 (1: 수학 좌표, 2: 경위도): "))
    function = int(input("원하는 기능을 선택하세요 (1: 두 점사이의 거리 및 방위각 계산 2: 점에서 방위각으로 좌표 구하기: "))

    if function == 1:
        if coordinate_system == 1:
            # Cartesian coordinates
            x1, y1 = map(float, input("A 지점의 x좌표와 y좌표를 입력하세요 (공백으로 구분): ").split())
            x2, y2 = map(float, input("B 지점의 x좌표와 y좌표를 입력하세요 (공백으로 구분): ").split())

            distance, distance_x, distance_y = calculate_distance(x1, y1, x2, y2)
            print("두 점 사이의 거리:", distance)

            bearing = calculate_bearing(x1, y1, x2, y2)
            print("두 점 사이의 방위각:", bearing)

            #위거 ,경거 출력
            print("위거:", distance_y)
            print("경거:", distance_x)
            pass
        
        elif coordinate_system == 2:
            # Geographic coordinates (latitude and longitude)
            lat1, lon1 = map(float, input("A 지점의 위도와 경도를 입력하세요 (공백으로 구분): ").split())

            lat2, lon2 = map(float, input("B 지점의 위도와 경도를 입력하세요 (공백으로 구분): ").split())

            distance, distance_lat, distance_lon = calculate_distance_lat_lon(lat1, lon1, lat2, lon2)
            print("거리:", distance*1000, "m")

            # 북측 방위각 계산
            bearing = calculate_bearing_lat_lon(lat1, lon1, lat2, lon2)
            print("북측 방위각:", bearing, "도")

            #위거 ,경거 출력
            print("위거:", distance_lat*1000, "m")
            print("경거:", distance_lon*1000, "m")
            pass
        
    elif function == 2:
        if coordinate_system == 1:
            x1, y1 = map(float, input("A 지점의 x좌표와 y좌표를 입력하세요 (공백으로 구분): ").split())
            bearing, distance = map(float, input("방위각과 거리를 입력하세요 (공백으로 구분): ").split())
            
            x2, y2 = calculate_destination_coordinates(x1, y1, bearing, distance)
            
            #좌표  출력
            print("x좌표:", x2)
            print("y좌표:", y2)
            pass
        
        elif coordinate_system == 2:
            # Geographic coordinates (latitude and longitude)
            lat1, lon1 = map(float, input("A 지점의 위도와 경도를 입력하세요 (공백으로 구분): ").split())

            bearing, distance = map(float, input("방위각과 거리를 입력하세요 (공백으로 구분): ").split())
            lat2, lon2 = calculate_destination_coordinates_lat_lon(lat1, lon1, bearing, distance)

            #죄표  출력
            print("위도:", lat2, "도")
            print("경도:", lon2, "도")
            pass

    choice = input("다른 기능을 선택하시겠습니까? (y/n): ")
    if choice.lower() != "y":
        print("프로그램을 종료합니다.")
        break       
