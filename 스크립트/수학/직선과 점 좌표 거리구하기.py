import matplotlib.pyplot as plt

def calculate_point(x1, y1, x2, y2, x3, y3, distance):
    # 직선의 방정식 계산
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1

    # 직선과 점 (x3, y3) 사이의 거리 계산
    perpendicular_slope = -1 / slope
    perpendicular_intercept = y3 - perpendicular_slope * x3
    intersection_x = (perpendicular_intercept - intercept) / (slope - perpendicular_slope)
    intersection_y = slope * intersection_x + intercept

    # 점 p4의 좌표 계산
    diff_x = x3 - intersection_x
    diff_y = y3 - intersection_y
    length = (diff_x ** 2 + diff_y ** 2) ** 0.5
    ratio = distance / length
    p4_x = x3 + ratio * diff_x
    p4_y = y3 + ratio * diff_y

    return p4_x, p4_y
while True:
    
# 계산기능 선택
    print("1. 직선 A에서 점 P3에서 X만큼 떨어진 거리의 점 P4찾기")
    print("2. 점 P4에서 직선 A로 수직거리인 직선 A위의 좌표 P3 찾기")
    print("0. 프로그램 종료")

    choice = int(input("원하는 기능의 번호를 입력하세요: "))
    if choice == 0:
        break
    if choice == 1:
        x1, y1 = map(float, input("직선 A의 점 1의 좌표를 공백으로 구분하여 입력하세요: ").split())
        x2, y2 = map(float, input("직선 A의 점 2의 좌표를 공백으로 구분하여 입력하세요: ").split())
        x3, y3 = map(float, input("점 P3의 좌표를 공백으로 구분하여 입력하세요: ").split())
        distance = float(input("거리 X를 입력하세요: "))

        p4_x, p4_y = calculate_point(x1, y1, x2, y2, x3, y3, distance)
        print("점 P4의 좌표:", p4_x, p4_y)

        # 그래프 표시
        plt.plot([x1, x2], [y1, y2], '-o', label='Line through (x1, y1) and (x2, y2)')
        plt.plot(x3, y3, 'ro', label='Point (x3, y3)')
        plt.plot(p4_x, p4_y, 'go', label='Point p4')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.legend()
        plt.title('Line and Points')
        plt.grid(True)
        plt.show()

    elif choice == 2:
        x1, y1 = map(float, input("직선 A의 점 1의 좌표를 공백으로 구분하여 입력하세요: ").split())
        x2, y2 = map(float, input("직선 A의 점 2의 좌표를 공백으로 구분하여 입력하세요: ").split())
        x4, y4 = map(float, input("점 P4의 좌표를 공백으로 구분하여 입력하세요: ").split())

        # 직선의 방정식 계산
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1

        # 수직거리인 직선 A 위의 좌표 P3 계산
        perpendicular_slope = -1 / slope
        perpendicular_intercept = y4 - perpendicular_slope * x4
        intersection_x = (perpendicular_intercept - intercept) / (slope - perpendicular_slope)
        intersection_y = slope * intersection_x + intercept

        print("점 P3의 좌표:", intersection_x, intersection_y)

        # 그래프 표시
        plt.plot([x1, x2], [y1, y2], '-o', label='Line through (x1, y1) and (x2, y2)')
        plt.plot(x4, y4, 'ro', label='Point P4')
        plt.plot(intersection_x, intersection_y, 'go', label='Point P3')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.legend()
        plt.title('Line and Points')
        plt.grid(True)
        plt.show()
