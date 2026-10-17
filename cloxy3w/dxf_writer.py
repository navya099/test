"""
dxf_writer.py - 원본(CLOXY) DXF 와 같은 레이어/라벨 체계로, 올바른 기하의 DXF(AC1009) 를 출력한다.

원본 TEST.DXF 분석 결과(레이어):
  OUTSIDE / CENTER / INSIDE : 전반 완화곡선 POLYLINE(BTC→BCC), 후반 완화곡선 POLYLINE(ETC→ECC), 원곡선 ARC
  CHAIN  : 중앙선의 chain 측점마다 길이 2 m 의 직교 눈금(LINE), 100 m 마다 반지름 1 m 원(CIRCLE)
  GTXT   : 라벨 TEXT (높이 1.5) — "BTCo STA. 11K 987.539" 등 12개 + "B.C STA." "E.C STA."
  DLINE  : 라벨 인출선 (바깥선 30 m, 중앙선 30+D/2, 안쪽선 30 m)
  COORDX / COORDY : 100 m 간격 좌표 격자선과 숫자 라벨(높이 5)

원본과 다른 점(의도적): 후반부를 거울상으로 그리고 ARC 중심/각이 어긋나던 오류를 바로잡아
실제 기하(진입 접선 +y, IP 원점의 로컬 좌표 또는 프로젝트 좌표)로 그린다.
"""
from __future__ import annotations
import copy
import math
from ip2_engine import solve_curve, frame, circle_center, station_coord
from out_writer import fF, kmsplit

LEADER = 30.0          # 인출선 기본 길이
TEXT_H = 1.5           # 라벨 높이
TICK = 2.0             # chain 눈금 길이
VSTEP = 0.5            # 선형 꼭짓점 간격 (원본과 동일)


class Dxf:
    def __init__(self):
        self.L = []

    def add(self, code: int, val):
        self.L.append(f"{code:3d}")
        self.L.append(val if isinstance(val, str) else str(val))

    def f(self, v):                      # 19.11 Fortran 서식
        return fF(v, 19, 11)

    def begin(self):
        for c, v in ((0, "SECTION"), (2, "HEADER"), (9, "$ACADVER"), (1, "AC1009"), (0, "ENDSEC"),
                     (0, "SECTION"), (2, "ENTITIES")):
            self.add(c, v)

    def end(self):
        self.add(0, "ENDSEC")
        self.add(0, "EOF")

    def polyline(self, layer, pts):
        self.add(0, "POLYLINE"); self.add(8, layer); self.add(66, "     1")
        self.add(10, "0.0"); self.add(20, "0.0"); self.add(30, "0.0")
        for x, y in pts:
            self.add(0, "VERTEX"); self.add(8, layer)
            self.add(10, self.f(x)); self.add(20, self.f(y)); self.add(30, "0.0")
        self.add(0, "SEQEND"); self.add(8, layer)

    def arc(self, layer, c, r, a1, a2):
        self.add(0, "ARC"); self.add(8, layer)
        self.add(10, self.f(c[0])); self.add(20, self.f(c[1])); self.add(30, "0.0")
        self.add(40, self.f(r)); self.add(50, self.f(a1)); self.add(51, self.f(a2))

    def line(self, layer, p, q):
        self.add(0, "LINE"); self.add(8, layer)
        self.add(10, self.f(p[0])); self.add(20, self.f(p[1])); self.add(30, "0.0")
        self.add(11, self.f(q[0])); self.add(21, self.f(q[1])); self.add(31, "0.0")

    def circle(self, layer, c, r):
        self.add(0, "CIRCLE"); self.add(8, layer)
        self.add(10, self.f(c[0])); self.add(20, self.f(c[1])); self.add(30, "0.0"); self.add(40, f"{r:.1f}")

    def text(self, pos, h, s, rot, right=False, layer="GTXT"):
        self.add(0, "TEXT"); self.add(8, layer)
        if right:      # 원본: 오른쪽 정렬(72=2) 은 정렬점을 11/21 에 기록
            self.add(10, "0.0"); self.add(20, "0.0"); self.add(30, "0.0")
        else:
            self.add(10, self.f(pos[0])); self.add(20, self.f(pos[1])); self.add(30, "0.0")
        self.add(40, f"{h:.1f}"); self.add(1, s); self.add(50, f"{rot % 360.0:15.10f}")
        self.add(72, "  2" if right else "  0"); self.add(73, "  0")
        if right:
            self.add(11, self.f(pos[0])); self.add(21, self.f(pos[1])); self.add(31, "0.0")

    def render(self) -> str:
        return "\r\n".join(self.L) + "\r\n"


# ------------------------------------------------------------------ 기하 보조
def _sta_label(name: str, sta: float) -> str:
    km, m = kmsplit(sta)
    return f"{name} STA. {km:2d}K{fF(m, 8, 3)}"


def _local_input(inp):
    """IP 를 원점, 진입 접선을 +y 로 하는 로컬 입력으로 변환 (회전 방향 유지)"""
    g = copy.copy(inp)
    right = ((inp.az_in_deg - inp.az_out_deg) % 360.0) > 180.0 if inp.az_in_deg is not None else False
    g.ip_n = g.ip_e = 0.0
    g.az_in_deg = 0.0
    g.az_out_deg = g.ia_deg if right else 360.0 - g.ia_deg
    return g


def _xy(cv, ln, s, fr):
    n, e, _ = station_coord(cv, ln, s, fr)
    return (e, n)                      # DXF: x = 동(E), y = 북(N)


def _poly_stations(a, b, extra):
    k = math.ceil(a / VSTEP - 1e-9)
    out = []
    while k * VSTEP < b - 1e-9:
        out.append(k * VSTEP)
        k += 1
    return sorted(set([a, b] + out + list(extra)))


def _tangent(cv, ln, s, fr):
    d = 1e-3
    p, q = _xy(cv, ln, s - d, fr), _xy(cv, ln, s + d, fr)
    h = math.hypot(q[0] - p[0], q[1] - p[1])
    return ((q[0] - p[0]) / h, (q[1] - p[1]) / h)


def _ang(u):
    return math.degrees(math.atan2(u[1], u[0])) % 360.0


# ------------------------------------------------------------------ IP 하나
def build_ip(d: Dxf, inp, mode: str = "local", grid: bool = True):
    """한 IP 의 엔티티를 d 에 추가.  mode: 'local'(IP 원점, 진입접선 +y) | 'global'(프로젝트 좌표)"""
    g = _local_input(inp) if mode == "local" else inp
    cv = solve_curve(g)
    fr = frame(cv)
    right = fr["s_turn"] < 0
    O = circle_center(cv, fr)
    O = (O[1], O[0])
    names = ("outside", "center", "inside")
    layer = {"outside": "OUTSIDE", "center": "CENTER", "inside": "INSIDE"}
    half = inp.D / 2
    pts_all = []

    def emit_line(nm):
        ln = cv.lines[nm]
        p1 = [_xy(cv, ln, s, fr) for s in _poly_stations(ln.BTC, ln.BCC, (cv.BC,))]
        p2 = [_xy(cv, ln, s, fr) for s in sorted(_poly_stations(ln.ECC, ln.ETC, (cv.EC,)), reverse=True)]
        d.polyline(layer[nm], p1)
        d.polyline(layer[nm], p2)
        a_b = math.degrees(math.atan2(p1[-1][1] - O[1], p1[-1][0] - O[0])) % 360.0     # BCC
        a_e = math.degrees(math.atan2(p2[-1][1] - O[1], p2[-1][0] - O[0])) % 360.0     # ECC
        (d.arc(layer[nm], O, ln.R, a_e, a_b) if right else d.arc(layer[nm], O, ln.R, a_b, a_e))
        pts_all.extend(p1 + p2)

    emit_line("outside")
    emit_line("center")

    # CHAIN: 중앙선의 chain 눈금과 100 m 마다 원
    c = cv.lines["center"]
    chain = inp.sta_step
    k = math.ceil(c.BTC / chain - 1e-9)
    while k * chain <= c.ETC + 1e-9:
        s = k * chain
        P = _xy(cv, c, s, fr)
        t = _tangent(cv, c, s, fr)
        nrm = (-t[1], t[0])
        d.line("CHAIN", (P[0] + nrm[0] * TICK / 2, P[1] + nrm[1] * TICK / 2),
               (P[0] - nrm[0] * TICK / 2, P[1] - nrm[1] * TICK / 2))
        if abs(s / 100.0 - round(s / 100.0)) < 1e-9:
            d.circle("CHAIN", P, 1.0)
        k += 1

    # GTXT/DLINE: 라벨 + 인출선
    def label(nm, name, sta, point_sta=None):
        ln = cv.lines[nm]
        s = sta if point_sta is None else point_sta
        P = _xy(cv, ln, s, fr)
        t = _tangent(cv, ln, s, fr)
        left = (-t[1], t[0])
        outward = (left[0] * (1 if right else -1), left[1] * (1 if right else -1))   # 원곡선 중심 반대쪽
        inside = nm == "inside"
        u = (-outward[0], -outward[1]) if inside else outward
        alpha = _ang(u)
        ln_len = LEADER + (half if nm == "center" else 0.0)
        d.line("DLINE", P, (P[0] + u[0] * ln_len, P[1] + u[1] * ln_len))
        nrm = (-u[1], u[0])                                   # 인출선을 +90° 회전한 방향
        d0 = 2.0 + (half if nm == "center" else 0.0)
        sign = -0.5 if inside else 0.5
        pos = (P[0] + u[0] * d0 + nrm[0] * sign, P[1] + u[1] * d0 + nrm[1] * sign)
        d.text(pos, TEXT_H, _sta_label(name, sta), alpha + (180.0 if inside else 0.0), right=inside)
        pts_all.extend([P, (P[0] + u[0] * ln_len, P[1] + u[1] * ln_len), pos])

    for nm, tag in (("outside", "o"), ("center", "c")):
        ln = cv.lines[nm]
        for key, sta in (("BTC", ln.BTC), ("BCC", ln.BCC), ("ETC", ln.ETC), ("ECC", ln.ECC)):
            label(nm, key + tag, sta)
    ln = cv.lines["inside"]
    for key, sta in (("BTC", ln.BTC), ("BCC", ln.BCC), ("ETC", ln.ETC), ("ECC", ln.ECC)):
        label("inside", key + "i", sta)
    label("center", "E.C", cv.EC)
    label("center", "B.C", cv.BC)
    emit_line("inside")

    # 좌표 격자 (로컬 좌표계에서만)
    if mode == "local" and grid:
        xs = [p[0] for p in pts_all]; ys = [p[1] for p in pts_all]
        x0, x1 = math.floor(min(xs) / 100) * 100, math.ceil(max(xs) / 100) * 100
        y0, y1 = math.floor(min(ys) / 100) * 100, math.ceil(max(ys) / 100) * 100
        y = y0
        while y <= y1 + 1e-9:
            d.line("COORDY", (x0, y), (x1, y))
            d.text((x0 + 3.0, y + 3.0), 5.0, f"{int(y):7d}", 0.0)
            y += 100
        x = x0
        while x <= x1 + 1e-9:
            d.line("COORDX", (x, y0), (x, y1))
            d.text((x - 3.0, y1 - 3.0), 5.0, f"{int(x):7d}", 90.0, right=True)
            x += 100
    return cv


def render_dxf(inputs, mode: str = "local", ip_no=None, grid: bool = True) -> str:
    """local: ip_no 로 지정한 IP 하나(기본: 첫 IP) / global: 모든 IP 를 한 파일에"""
    d = Dxf()
    d.begin()
    if mode == "local":
        inp = next((i for i in inputs if ip_no in (None, i.ip_no)), inputs[0])
        build_ip(d, inp, "local", grid)
    else:
        for inp in inputs:
            build_ip(d, inp, "global", grid)
    d.end()
    return d.render()


def write_dxf(path: str, inputs, **kw):
    with open(path, "wb") as f:
        f.write(render_dxf(inputs, **kw).encode("cp949"))
