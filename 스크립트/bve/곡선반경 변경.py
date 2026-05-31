import math
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import numpy as np


"""
cl= r*theta
ia =

"""

def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2

def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing

BC_input = input("기존 곡선 시점 측점을 입력하세요 (기본값 123.456): ")
BC = float(BC_input) if BC_input else 123.456
EC_input = input("기존 곡선 종점 측점을 입력하세요 (기본값 789.123): ")
EC = float(EC_input) if EC_input else 789.123
R_input = input("기존 곡선 반경을 입력하세요 (기본값 600): ")
R = float(R_input) if R_input else 600
NEW_R_input = input("새 곡선 반경을 입력하세요 (기본값 700): ")
NEW_R = float(NEW_R_input) if NEW_R_input else 700

CL= EC-BC
IA = CL/R
TL = R * math.tan(IA/2)

IA_DEGREE = math.degrees(IA)
IP_STA = BC + TL

NEW_TL = NEW_R * math.tan(IA/2)
NEW_CL = NEW_R * IA

NEW_BC = IP_STA - NEW_TL
NEW_EC = NEW_BC + NEW_CL

BC_XY = (0,0)
O_XY = (R,0)
IP_XY = (0,TL)
EC_XY = calculate_destination_coordinates(R, 0, 180-IA_DEGREE, R)


BP_IP_BREAING = calculate_bearing(0, 0, 0, TL)
print("BP_IP_BREAING : ",BP_IP_BREAING)
IP_EP_BREAING = calculate_bearing(0, TL, 0, TL)

O_BC_BEARING = calculate_bearing(R,0,BC_XY[0],BC_XY[1])
O_BC_BEARING_RAD = math.radians(O_BC_BEARING)

O_SP_BEARING = O_BC_BEARING - IA_DEGREE/2
O_SP_BEARING_RAD = math.radians(O_BC_BEARING)

print("O_BC_BEARING : ",O_BC_BEARING)
print("O_BC_BEARING_RAD : ",O_BC_BEARING_RAD)
print("O_SP_BEARING : ",O_SP_BEARING)
print("O_SP_BEARING_RAD : ",O_SP_BEARING_RAD)

SP_XY = calculate_destination_coordinates(R, 0, O_SP_BEARING, R)

print("IP_XY" ,IP_XY)
print("O_XY" ,O_XY)
print("EC_XY" ,EC_XY)
print("SP_XY" ,SP_XY)



print("\n변경전\n")
print("IA : ",IA)
print("CL : ",CL)
print("TL : ",TL)
print("IP 정측점 : ",IP_STA)

print("\n변경후\n")
print("IA : ",IA)
print("CL : ",NEW_CL)
print("TL : ",NEW_TL)
print("새 BC : ",NEW_BC)
print("새 EC : ",NEW_EC)


print("\nOPENBVE 구문 복사\n")
print(NEW_BC,",.CURVE ",NEW_R)
print(NEW_EC,",.CURVE 0")

# Plot the arc and points
plt.figure()
plt.scatter(*zip(*[BC_XY, IP_XY, EC_XY,O_XY,SP_XY]), color='red', label='Given Points', marker='o')
# Connect the points with a line
plt.plot(*zip(*[BC_XY, IP_XY, EC_XY]), linestyle='-', color='RED', label='Connecting Line')



plt.text(*BC_XY, 'BC', fontsize=12, ha='right')
plt.text(*IP_XY, 'IP', fontsize=12, ha='right')
plt.text(*EC_XY, 'EC', fontsize=12, ha='right')
plt.text(*SP_XY, 'SP', fontsize=12, ha='right')
plt.text(*O_XY, 'O', fontsize=12, ha='right')
plt.text(*IP_XY, f'IA: {IA_DEGREE:.2f}', fontsize=12, ha='left')
plt.title('Three-Point Arc')
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.legend()
plt.grid(True)
plt.show()
