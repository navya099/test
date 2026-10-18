"""
ip2_engine.py - 레거시 포트란 'I.P 2' (CLOTHOID CURVE) 계산 엔진의 파이썬 재구현

샘플(IP2.DAT / IP2.OUT) 블랙박스 분석으로 역추정한 모델:
  * 기준선(측량중심) = 반경 R0 의 기존 단곡선 (IP, IA 로 정의)
  * 3개 선(외측/중앙/내측)은 같은 원 중심 O 를 공유 (동심원)
  * 외측선: 입력 완화곡선장 L 로 R_out 을 풀고 (R + dR = R0 + B)
  * 중앙선 R_c = R_out - A",  내측선 R_in = R_c - B
  * 중앙/내측선의 L 은 R_i + dR_i = R0 -/+ ... 조건으로 역산
  * 측점은 기준선 위의 측점; 직선부는 접선 수직, 원곡선부는 O 로부터의 방사선으로 대응
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field


def brentq(f, a, b, xtol=1e-13, maxiter=200):
    """scipy 없이 쓰는 근 찾기 (이분법 + 시컨트 혼합, 부호가 다른 구간 필요)"""
    fa, fb = f(a), f(b)
    if fa == 0:
        return a
    if fb == 0:
        return b
    if fa * fb > 0:
        raise ValueError("f(a) and f(b) must have different signs")
    for _ in range(maxiter):
        c = b - fb * (b - a) / (fb - fa)                # 시컨트(거짓위치)
        if not (min(a, b) < c < max(a, b)):
            c = (a + b) / 2
        fc = f(c)
        if fc == 0 or abs(b - a) < xtol * max(1.0, abs(c)):
            return c
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
        if abs(fb - fa) < 1e-300:
            break
        m = (a + b) / 2                                  # 수렴이 느리면 이분법 한 번
        fm = f(m)
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return (a + b) / 2


# ----------------------------------------------------------------- 각도 유틸
def packed_dms_to_deg(v: float) -> float:
    """DDD.MMSSss (예: 125.24033700 -> 125°24'03.37") -> 십진 도"""
    s = f"{abs(v):.8f}"
    d, f = s.split(".")
    mm = int(f[0:2])
    ss = int(f[2:4]) + int(f[4:8]) / 10000.0
    return math.copysign(int(d) + mm / 60 + ss / 3600, v)


def deg_to_dms(deg: float):
    d = int(deg)
    m = int((deg - d) * 60)
    s = ((deg - d) * 60 - m) * 60
    return d, m, s


# ------------------------------------------------------------ 클로소이드 기본
def clothoid_xy(l: float, R: float, L: float, terms: int = 8):
    """곡선장 l 에서의 (X, Y, phi).  phi = l^2 / (2 R L) (접선각, rad)"""
    phi = l * l / (2 * R * L)
    sx = sy = 0.0
    for n in range(terms):
        sx += (-1) ** n * phi ** (2 * n) / ((4 * n + 1) * math.factorial(2 * n))
        sy += (-1) ** n * phi ** (2 * n + 1) / ((4 * n + 3) * math.factorial(2 * n + 1))
    return l * sx, l * sy, phi


def clothoid_end(R: float, L: float):
    """SC 점 제원: X, Y, theta, dR(이정량), XM"""
    X, Y, th = clothoid_xy(L, R, L)
    dR = Y - R * (1 - math.cos(th))
    XM = X - R * math.sin(th)
    return X, Y, th, dR, XM


# ------------------------------------------------------------------ 입력 모델
@dataclass
class IP2Input:
    ip_no: int
    R: float          # 기준 반경 R0
    L: float          # 외측선 완화곡선장
    B: float          # 선간 오프셋 (샘플: 2.2)
    A2: float         # A" 외측-중앙 반경차 (샘플: 2.72)
    D: float          # (샘플: 4.4 = 2B, 용도 미확정)
    ip_sta: float
    ia_deg: float
    sta_start: float
    sta_end: float
    sta_step: float
    coord_flag: str = "N"
    ip_n: float | None = None
    ip_e: float | None = None
    az_in_deg: float | None = None
    az_out_deg: float | None = None
    l_ref: str = "outside"      # 입력 L 이 어느 선의 완화곡선장인가: outside(원본 프로그램 방식)/center/inside


def parse_dat(text: str) -> IP2Input:
    """IP2.DAT 한 블록 파싱 (샘플 형식 기준)"""
    lines = [ln.rstrip("\r\n") for ln in text.splitlines() if ln.strip() != ""]
    f = lambda s: [float(x) for x in s.split()]
    # lines[0]: IP 개수(추정)
    r = f(lines[1])
    ip_no = int(r[0])
    R, L, B, A2, D = r[1:6]
    ip_sta, ia_packed = f(lines[2])
    s0, s1, ds = f(lines[3])
    flag = lines[4].strip()
    inp = IP2Input(ip_no, R, L, B, A2, D, ip_sta, packed_dms_to_deg(ia_packed),
                   s0, s1, ds, flag)
    if flag.upper().startswith("Y") and len(lines) > 5:
        n, e, a1, a2 = f(lines[5])
        inp.ip_n, inp.ip_e = n, e
        inp.az_in_deg = a1      # 방위각은 십진 도 (좌표 대조로 확인)
        inp.az_out_deg = a2
    return inp


def parse_dat_multi(text: str) -> list:
    """IP 여러 개가 든 DAT (1행 = IP 개수, 이후 IP별 4~5행 블록)"""
    lines = [ln.rstrip("\r\n") for ln in text.splitlines() if ln.strip() != ""]
    f = lambda s: [float(x) for x in s.split()]
    n = int(float(lines[0].split()[0]))
    i, out = 1, []
    for _ in range(n):
        r = f(lines[i]); ip_sta, ia_packed = f(lines[i + 1]); s0, s1, ds = f(lines[i + 2])
        flag = lines[i + 3].strip()
        inp = IP2Input(int(r[0]), r[1], r[2], r[3], r[4], r[5], ip_sta,
                       packed_dms_to_deg(ia_packed), s0, s1, ds, flag)
        i += 4
        if flag.upper().startswith("Y"):
            a = f(lines[i]); i += 1
            inp.ip_n, inp.ip_e, inp.az_in_deg, inp.az_out_deg = a[0], a[1], a[2], a[3]
        out.append(inp)
    return out


# --------------------------------------------------------------------- 선 정의
@dataclass
class Line:
    name: str
    y_ex: float       # 기존선(중앙)이 이 선의 접선에서 원중심 쪽으로 떨어진 거리
    R: float
    L: float
    X: float
    Y: float
    theta: float
    dR: float
    XM: float
    YM: float
    P: float
    sigma: float
    CL: float
    BTC: float
    BCC: float
    ECC: float
    ETC: float


@dataclass
class Curve:
    inp: IP2Input
    ia: float
    TL0: float
    CL0: float
    SL0: float
    BC: float
    EC: float
    lines: dict = field(default_factory=dict)


def solve_curve(inp: IP2Input) -> Curve:
    """세 선(외측/중앙/내측)은 같은 원 중심을 공유한다.
      직선부 오프셋 = D/2 (외측 +D/2, 내측 -D/2)  → 각 선의 YM = R0 ± D/2
      원곡선부 반경 : R_out = R_c + A",  R_in = R_c - B   (B, A" 는 확폭이 반영된 고정 입력값)
    입력 L 은 inp.l_ref 로 지정한 선의 완화곡선장이며, 그 선의 R 을 풀고 나머지 R, L 을 역산한다.
    (원본 프로그램의 입력 L 은 outside 기준 — 21개 IP 에서 확인)"""
    ia = math.radians(inp.ia_deg)
    R0, B = inp.R, inp.B          # B: 내측궤도
    t = math.tan(ia / 2)
    TL0, CL0 = R0 * t, R0 * ia
    SL0 = R0 * (1 / math.cos(ia / 2) - 1)
    BC = inp.ip_sta - TL0
    EC = BC + CL0
    cv = Curve(inp, ia, TL0, CL0, SL0, BC, EC)

    h = inp.D / 2
    ref = getattr(inp, "l_ref", "outside")
    y_ex = {"outside": +h, "center": 0.0, "inside": -h}            # 기존선(중앙)이 접선에서 원중심 쪽으로 떨어진 거리
    ym = {k: R0 + v for k, v in y_ex.items()}
    off = {"outside": inp.A2, "center": 0.0, "inside": -B}          # R_i = R_c + off_i
    R_ref = brentq(lambda R: R + clothoid_end(R, inp.L)[3] - ym[ref], 50, 1e4)
    R_c = R_ref - off[ref]
    for name in ("outside", "center", "inside"):
        R = R_c + off[name]
        if name == ref:
            L = inp.L
        else:
            L = brentq(lambda LL: R + clothoid_end(R, LL)[3] - ym[name], 1, R)
        X, Y, th, dR, XM = clothoid_end(R, L)
        sig = ia - 2 * th
        cv.lines[name] = Line(
            name, y_ex[name], R, L, X, Y, th, dR, XM, ym[name], ym[name] * t + XM, sig, R * sig,
            BC - XM, BC + R0 * th, EC - R0 * th, EC + XM)
    return cv


# ---------------------------------------------------------- 측점별 계산
def _solve_l_for_x(x, ln: Line):
    return brentq(lambda l: clothoid_xy(l, ln.R, ln.L)[0] - x, 0.0, ln.L)


def _solve_l_radial(psi, ln: Line):
    """원중심 O 에서 방사각 psi 인 방향에 놓이는 클로소이드 점의 곡선장"""
    if psi >= ln.theta:          # 표기 반올림으로 SC 경계를 살짝 넘는 경우
        return ln.L
    def g(l):
        X, Y, _ = clothoid_xy(l, ln.R, ln.L)
        return math.atan2(X - ln.XM, ln.YM - Y) - psi
    return brentq(g, 0.0, ln.L)


def station_point(cv: Curve, ln: Line, s: float):
    """기준선 측점 s 에 대응하는 선 ln 위의 점. 반환 dict"""
    R0 = cv.inp.R
    if s <= cv.BC:                                   # 직선부 + 전방 완화부(접선 수직 대응)
        x = s - ln.BTC
        l = _solve_l_for_x(x, ln) if x > 0 else 0.0
        zone = "A"
    elif s < ln.BCC:                                 # 방사선 대응
        l = _solve_l_radial((s - cv.BC) / R0, ln)
        zone = "B"
    elif s <= ln.ECC - 5e-4:      # 3자리 반올림된 ECC 측점은 후반 완화곡선 쪽으로 처리
        l, zone = ln.L, "C"
    elif s < cv.EC:
        l = _solve_l_radial((cv.EC - s) / R0, ln)
        zone = "D"
    else:
        x = ln.ETC - s
        l = _solve_l_for_x(x, ln) if x > 0 else 0.0
        zone = "E"
    X, Y, phi = clothoid_xy(l, ln.R, ln.L)
    if zone in "AE":
        xs = (s - ln.BTC) if zone == "A" else (ln.ETC - s)
        if xs < 0:                                  # 완화곡선 밖의 직선부: 접선 위로 연장
            X, Y, phi = xs, 0.0, 0.0
    if zone in "AE":
        S = abs(Y - ln.y_ex)
    else:
        rho = math.hypot(X - ln.XM, ln.YM - Y)
        S = abs(rho - R0)
    if phi > 1e-12:
        Tk = Y / math.sin(phi)
        U = Y / math.tan(phi)
        Tl = X - U
    else:
        Tk = Tl = U = 0.0
    return dict(s=s, l=l, zone=zone, X=X, Y=Y, Tk=Tk, Tl=Tl, S=S, phi=phi)


# ---------------------------------------------------------------- 좌표 계산
def _az_vec(az_deg):
    a = math.radians(az_deg)
    return math.cos(a), math.sin(a)        # (North, East)


def frame(cv: Curve):
    inp = cv.inp
    s_turn = 1 if ((inp.az_in_deg - inp.az_out_deg) % 360) < 180 else -1   # +1: 좌회전
    u1 = _az_vec(inp.az_in_deg)
    u2 = _az_vec(inp.az_out_deg)
    nc1 = _az_vec(inp.az_in_deg - 90 * s_turn)    # 접선 -> 원중심 방향 (진입)
    nc2 = _az_vec(inp.az_out_deg - 90 * s_turn)   # (진출)
    ip = (inp.ip_n, inp.ip_e)
    bc_g = (ip[0] - cv.TL0 * u1[0], ip[1] - cv.TL0 * u1[1])
    ec_g = (ip[0] + cv.TL0 * u2[0], ip[1] + cv.TL0 * u2[1])
    return dict(s_turn=s_turn, u1=u1, u2=u2, nc1=nc1, nc2=nc2, bc_g=bc_g, ec_g=ec_g)


def line_anchor(cv: Curve, ln: Line, fr):
    ts = (fr["bc_g"][0] - ln.XM * fr["u1"][0] - ln.y_ex * fr["nc1"][0],
          fr["bc_g"][1] - ln.XM * fr["u1"][1] - ln.y_ex * fr["nc1"][1])
    te = (fr["ec_g"][0] + ln.XM * fr["u2"][0] - ln.y_ex * fr["nc2"][0],
          fr["ec_g"][1] + ln.XM * fr["u2"][1] - ln.y_ex * fr["nc2"][1])
    return ts, te


def circle_center(cv: Curve, fr):
    c = cv.lines["center"]
    ts, _ = line_anchor(cv, c, fr)
    return (ts[0] + c.XM * fr["u1"][0] + c.YM * fr["nc1"][0],
            ts[1] + c.XM * fr["u1"][1] + c.YM * fr["nc1"][1])


def station_coord(cv: Curve, ln: Line, s: float, fr=None):
    fr = fr or frame(cv)
    ts, te = line_anchor(cv, ln, fr)
    p = station_point(cv, ln, s)
    R0 = cv.inp.R
    if p["zone"] in "AB":
        n = ts[0] + p["X"] * fr["u1"][0] + p["Y"] * fr["nc1"][0]
        e = ts[1] + p["X"] * fr["u1"][1] + p["Y"] * fr["nc1"][1]
    elif p["zone"] in "DE":
        n = te[0] - p["X"] * fr["u2"][0] + p["Y"] * fr["nc2"][0]
        e = te[1] - p["X"] * fr["u2"][1] + p["Y"] * fr["nc2"][1]
    else:                                          # 원곡선부: O 기준 방사
        o = circle_center(cv, fr)
        psi = (s - cv.BC) / R0
        az = cv.inp.az_in_deg + 90 * fr["s_turn"] - math.degrees(psi) * fr["s_turn"]
        v = _az_vec(az)
        n, e = o[0] + ln.R * v[0], o[1] + ln.R * v[1]
    return n, e, p


# ------------------------------------------------------- 출력 측점 목록
def station_list(cv: Curve, ln: Line):
    inp = cv.inp
    pts = {round(ln.BTC, 3): "BTC", round(cv.BC, 3): "BC", round(ln.BCC, 3): "BCC",
           round(ln.ECC, 3): "ECC", round(cv.EC, 3): "EC", round(ln.ETC, 3): "ETC"}
    s = inp.sta_start
    regular = []
    while s <= inp.sta_end + 1e-9:
        if ln.BTC < s < ln.ETC and not (ln.BCC < s < ln.ECC):   # 원곡선부 내부는 표에서 생략
            regular.append(round(s, 3))
        s += inp.sta_step
    allp = sorted(set(list(pts) + regular))
    return [(x, pts.get(x, "")) for x in allp]
