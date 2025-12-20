import math

from point2d import Point2d


def xm(x1, r, t):
    return x1 - (r * math.sin(t))

def dr(y1, r, t):
    return y1 + (r * math.cos(t)) - r

def w(r, dr, ia):
    return (r + dr) * math.tan(ia / 2)

def z1(dr1, dr2, ia):
    return (dr2 - dr1) / math.sin(ia)

def z2(dr1, dr2, ia):
    return (dr2 - dr1) / math.tan(ia)

def d(xm, w, z):
    return xm + w + z

def dms_to_rad(deg, minute, second):
    sign = -1 if deg < 0 else 1
    return math.radians(sign * (abs(deg) + minute/60 + second/3600))
# ------------------------
# 입력값
# ------------------------
r = 1200
IP = Point2d(218848.2178 ,434729.9024)
# 교각 IA (도분초 → rad)
ia = math.radians(59.48819023
)
h1 = math.radians(35 + 22/60 + 19/3600)
h2 = math.radians(90 - 114.116298)

# 완화곡선 종점 좌표
X1_S = 1883.918
Y1_S = 492.937

X1_E = 232
Y1_E = 7.476

# 접선각 (예: 클로소이드)
T_S = math.atan(X1_S / (2 * r))
T_E = math.atan(X1_E / (2 * r))

# ------------------------
# 계산
# ------------------------
XM_S = xm(X1_S, r, T_S)
XM_E = xm(X1_E, r, T_E)

DR_S = dr(Y1_S, r, T_S)
DR_E = dr(Y1_E, r, T_E)

W = w(r, DR_S, ia)

Z1 = z1(DR_S, DR_E, ia)
Z2 = z2(DR_S, DR_E, ia)

D1 = d(XM_S, W, Z1)
D2 = d(XM_E, W, -Z2)

BTC = IP.moved(h1 + math.pi, D1)
BCC = BTC.moved(h1, X1_S)
BCC.move(h1 - math.pi /2, Y1_S)
ETC = IP.moved(h2, D2)
ECC = ETC.moved(h2 + math.pi, X1_E)
ECC.move(h2 - math.pi / 2, Y1_E)

# ------------------------
# 출력
# ------------------------
print(f'T1 = {math.degrees(T_S):.6f}')
print(f'XM1 = {XM_S:.6f}')
print(f'DR1 = {DR_S:.6f}')
print(f'W   = {W:.6f}')
print(f'Z1  = {Z1:.6f}')
print(f'D1  = {D1:.6f}')
print(f'T2 = {math.degrees(T_E):.6f}')
print(f'XM2 = {XM_E:.6f}')
print(f'DR2 = {DR_E:.6f}')
print(f'Z2  = {Z2:.6f}')
print(f'D2  = {D2:.6f}')

print(f'BTC  = {BTC.x:.4f},{BTC.y:.4f}')
print(f'BCC  = {BCC.x:.4f},{BCC.y:.4f}')
print(f'ECC  = {ECC.x:.4f},{ECC.y:.4f}')
print(f'ETC  = {ETC.x:.4f},{ETC.y:.4f}')