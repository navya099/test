"""
out_writer.py - ip2_engine 계산 결과를 원본(CLOXY) .OUT 텍스트 서식으로 출력한다.

서식은 TEST_1.OUT / A8C.OUT / IP2.OUT / 88.OUT 의 분석 결과에 맞춘다.
 * 인코딩 cp949, 줄바꿈 CRLF, IP 블록마다 form-feed(\\f) 로 시작
 * Fortran 스타일 숫자 (|값|<1 이면 앞의 0 생략: .049)
"""
from __future__ import annotations
import math
from ip2_engine import (solve_curve, frame, circle_center, station_point, station_coord,
                        station_list, deg_to_dms)

TITLE = "***  CLOTHOID CURVE  BY SeoYoung L.T.D  ***"


# ------------------------------------------------------------- 숫자 서식
def fF(x: float, w: int, d: int) -> str:
    """Fortran Fw.d : 앞 0 생략, 오른쪽 정렬"""
    s = f"{x:.{d}f}"
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s.rjust(w)


def fdms(deg: float) -> str:
    """도-분-초 (초는 F5.2)  예: ' 0-58-40.26', '10- 5-54.54'"""
    tot = round(deg * 3600 * 100) / 100.0
    d = int(tot // 3600)
    rem = tot - d * 3600
    m = int(rem // 60)
    s = round(rem - m * 60, 2)
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        d += 1
    return f"{d}-{m:2d}-{fF(s, 5, 2)}"


def kmsplit(sta: float, nd: int = 3):
    """km 와 m 로 분리. 표시 자릿수(nd)로 먼저 반올림해서 1000.000 / 999.9999 같은 경계 오류를 막는다
    (원본은 정확히 km 경계의 측점에서 'K*******' 로 깨져 출력됨)"""
    scale = 10 ** nd
    t = round(sta * scale)
    km = t // (1000 * scale)
    return km, (t - km * 1000 * scale) / scale


def km_hdr(sta: float, wm: int, dm: int) -> str:
    km, m = kmsplit(sta, dm)
    return f"{km:2d} Km{fF(m, wm, dm)}"


# ------------------------------------------------------------ 보조 계산
def line_summary(ln) -> dict:
    """요약표 한 열(선)에 필요한 모든 값"""
    X, Y, th = ln.X, ln.Y, ln.theta
    Z = math.hypot(X, Y)
    tau = math.atan2(Y, X)
    U = Y / math.tan(th)
    Tk = Y / math.sin(th)
    Tl = X - U
    N = Y / math.cos(th)
    T = X + N * math.sin(th)
    return dict(R=ln.R, L=ln.L, DR=ln.dR, X=X, Y=Y, THETA=th, XM=ln.XM, YM=ln.YM, Z=Z, TAU=tau,
                U=U, Tk=Tk, Tl=Tl, N=N, T=T, P=ln.P, SIGMA=ln.sigma, CL=ln.CL,
                SIGMAL=ln.CL + 2 * ln.L, BTC=ln.BTC, BCC=ln.BCC, ECC=ln.ECC, ETC=ln.ETC)


_ROWS = [  # (표시 라벨, 키, 종류)
    ("R   (m)", "R", "f"), ("L   (m)", "L", "f"), ("DR  (m)", "DR", "f"), ("X   (m)", "X", "f"),
    ("Y   (m)", "Y", "f"), ("THETA", "THETA", "a"), ("XM  (m)", "XM", "f"), ("YM  (m)", "YM", "f"),
    ("Z   (m)", "Z", "f"), ("TAU", "TAU", "a"), ("U   (m)", "U", "f"), ("Tk  (m)", "Tk", "f"),
    ("Tl  (m)", "Tl", "f"), ("N   (m)", "N", "f"), ("T   (m)", "T", "f"), ("P   (m)", "P", "f"),
    ("SIGMA", "SIGMA", "a"), ("CL  (m)", "CL", "f"), ("SIGMAL(m)", "SIGMAL", "f"),
]
_STA_ROWS = [("B.T.C", "BTC"), ("B.C.C", "BCC"), ("E.C.C", "ECC"), ("E.T.C", "ETC")]
_NAMES = ["outside", "center", "inside"]


def _row(label: str, cells) -> str:
    return " " * 9 + label.ljust(10) + "".join(c.rjust(20) for c in cells)


def summary_block(cv, no: int) -> list:
    inp = cv.inp
    eq = "    " + "=" * 80
    dash = "    " + "-" * 80
    out = ["\f", "", " " * 24 + TITLE, "", "", f"       IP NO. ={no:6d}", eq]
    out.append(f"       R  ={fF(inp.R, 9, 3)} m             L  ={fF(inp.L, 9, 3)} m"
               f"             IA ={fdms(math.degrees(cv.ia)).rjust(13)}")
    out.append(f"       D  ={fF(inp.D, 9, 3)} m             A\" ={fF(inp.A2, 9, 3)} m"
               f"             B  ={fF(inp.B, 9, 3)} m")
    out.append(f"       TL ={fF(cv.TL0, 9, 3)} m             CL ={fF(cv.CL0, 9, 3)} m"
               f"             SL ={fF(cv.SL0, 9, 3)} m")
    out.append(f"       IP = {km_hdr(inp.ip_sta, 10, 4)}        BC = {km_hdr(cv.BC, 9, 4)}"
               f"         EC = {km_hdr(cv.EC, 9, 4)}")
    out.append(eq)
    out.append(" " * 32 + "OUTSIDE              CENTER              INSIDE")
    out.append(eq)
    sm = {n: line_summary(cv.lines[n]) for n in _NAMES}
    for i, (lab, key, kind) in enumerate(_ROWS):
        cells = []
        for n in _NAMES:
            v = sm[n][key]
            cells.append(fF(v, 0, 3) if kind == "f" else fdms(math.degrees(v)))
        out.append(_row(lab, cells))
        out.append(dash)
    out[-1] = eq
    for i, (lab, key) in enumerate(_STA_ROWS):
        out.append(_row(lab, [km_hdr(sm[n][key], 8, 3) for n in _NAMES]))
        out.append(dash if i < 3 else eq)
    return out



def _stations(cv, ln, interior: bool):
    """[(정확한 측점, 태그)] 특수점은 반올림 전 값 유지.
    원본 동작: 전이곡선부 일반 측점 = sta_start + k*chain, 원곡선부(BCC~ECC) 일반 측점 = chain 의 배수(0 기준)"""
    inp = cv.inp
    sp = {"BTC": ln.BTC, "BC": cv.BC, "BCC": ln.BCC, "ECC": ln.ECC, "EC": cv.EC, "ETC": ln.ETC}
    pts = [(v, k) for k, v in sp.items()]
    step = inp.sta_step
    k0 = math.ceil((ln.BTC - inp.sta_start) / step - 1e-9)
    s = inp.sta_start + max(k0, 0) * step
    while s <= ln.ETC + 1e-9:                                  # 전이곡선부 (start 기준)
        if (ln.BTC < s < ln.ETC and inp.sta_start - 1e-9 <= s <= inp.sta_end + 1e-9
                and not (ln.BCC < s < ln.ECC)):
            pts.append((s, ""))
        s += step
    if interior:                                               # 원곡선부 (0 기준)
        k = math.floor(ln.BCC / step) + 1
        while k * step < ln.ECC - 1e-9:
            if k * step > ln.BCC + 1e-9 and inp.sta_start - 1e-9 <= k * step <= inp.sta_end + 1e-9:
                pts.append((k * step, ""))
            k += 1
    return sorted(pts, key=lambda t: t[0])


# --------------------------------------------------------- 단위분포표
def _unit_rows(cv, ln):
    rows = []
    for s, tag in _stations(cv, ln, interior=False):
        p = station_point(cv, ln, s)
        rows.append((s, p))
    return rows


LEGACY_TK = 2.5e-5   # 원본의 TK/TL 분할 편향 (±2.5e-5·X, 합은 보존). 0 이면 정확식


def unit_table(cv, name: str, no: int, legacy: bool = True) -> list:
    ln = cv.lines[name]
    bar_eq, bar_d = "=" * 80, "-" * 80
    out = [""] * 8
    out += [" " * 23 + "UNIT DISTRIBUTION CLOTHOID CURVE", " " * 20 + "-" * 37, ""]
    out.append(f"    IP NO.={no:5d}" + " " * 53 + name.upper().ljust(10))
    out.append(bar_eq)
    ps = line_summary(ln)
    out.append(f"   R  ={fF(ln.R, 9, 3)} m" + " " * 14 + f"L  ={fF(ln.L, 9, 3)} m" + " " * 14
               + f"Y ={fF(ln.Y, 9, 3)} m")
    out.append(bar_d)
    out.append("  STATION          X         Y          TK         TL        S           PAI")
    out.append(bar_d)
    rows = _unit_rows(cv, ln)
    last_first = max(i for i, (s, _) in enumerate(rows) if s <= ln.BCC + 5e-4)
    for i, (s, p) in enumerate(rows):
        km, m = kmsplit(s)
        adj = LEGACY_TK * p["X"] if legacy else 0.0
        out.append(f"{km:3d}+{fF(m, 7, 3)}" + fF(p["X"], 11, 3) + fF(p["Y"], 10, 3) + fF(p["Tk"] - adj, 11, 3)
                   + fF(p["Tl"] + adj, 11, 3) + fF(p["S"], 10, 3) + fdms(math.degrees(p["phi"])).rjust(15))
        out.append(bar_eq if i == last_first else bar_d)
    return out


# ------------------------------------------------------------ 좌표표
_TAG = {"BTC": "BTC ", "BC": " BC ", "BCC": "BCC ", "ECC": "ECC ", "EC": " EC ", "ETC": "ETC "}


def _all_stations(cv, ln):
    return _stations(cv, ln, interior=True)


def circle_block(cv, fr) -> list:
    o = circle_center(cv, fr)
    return ["   center  CORDINATION of circle ", f"   x = {o[0]:12.4f}", f"   y = {o[1]:12.4f}"]


def coord_table(cv, name: str, fr) -> list:
    ln = cv.lines[name]
    eq, dash = " " * 10 + "=" * 51, " " * 10 + "-" * 51
    out = ["", "", "", " " * 22 + "CALCULATION OF CORDINATION ", "", "",
           " " * 14 + "( 측량중심 STATION에 대한 CLOTHOID 좌표  )", " " * 15 + f"{name} x, y", "",
           eq, " " * 10 + "|    STA.    |   X(north)    |   Y(earth)    |비고|", eq]
    for s, tag in _all_stations(cv, ln):
        n, e, _ = station_coord(cv, ln, s, fr)
        km, m = kmsplit(s)
        out.append(" " * 10 + "|" + f"{km:2d}K{fF(m, 7, 3)}  " + "|" + f"  {n:11.4f}  " + "|"
                   + f"  {e:11.4f}  " + "|" + _TAG.get(tag, "    ") + "|")
        out.append(dash)
    return out


# ---------------------------------------------------------------- 전체
def ip_block(cv, no: int, distribution: bool = True, coordinates: bool = True) -> list:
    out = summary_block(cv, no)
    if not distribution:
        return out
    for n in _NAMES:
        out += unit_table(cv, n, no)
    out += ["", "", "", " " * 27 + "END OF CALCULATION."]
    if coordinates and cv.inp.ip_n is not None:
        fr = frame(cv)
        out += ["", "", ""]
        for n in _NAMES:
            out += circle_block(cv, fr)
            out += coord_table(cv, n, fr)
    return out


def full_section(full) -> list:
    """BP ~ EP 전체 선형의 측점별 좌표 (직선부 포함). 좌측/중앙/우측 궤도 각각 한 표"""
    from fullalign import SIDES, SIDE_LABEL, SIDE_KO
    eq, dash = " " * 10 + "=" * 55, " " * 10 + "-" * 55
    out = ["\f", "", " " * 24 + TITLE, "", "", " " * 14 + "( 전체 선형 STATION 좌표 : BP ~ EP, 직선구간 포함 )"]
    for side in SIDES:
        out += ["", "", " " * 15 + f"{SIDE_LABEL[side].lower()} x, y   ({SIDE_KO[side]})", "", eq,
                " " * 10 + "|    STA.    |   X(north)    |   Y(earth)    |  비고  |", eq]
        for s, tag, ip in full.stations(side):
            n, e = full.point(side, s)
            km, m = kmsplit(s)
            note = tag if ip == 0 else f"{tag}{ip}"
            out.append(" " * 10 + "|" + f"{km:2d}K{fF(m, 7, 3)}  " + "|" + f"  {n:11.4f}  " + "|"
                       + f"  {e:11.4f}  " + "|" + note.ljust(8) + "|")
            out.append(dash)
    return out


def render(inputs, distribution: bool = True, coordinates: bool = True, full=None) -> str:
    lines = []
    for inp in inputs:
        cv = solve_curve(inp)
        lines += ip_block(cv, inp.ip_no, distribution, coordinates)
    if full is not None:
        lines += full_section(full)
    return "\r\n".join(lines) + "\r\n"


def write_out(path: str, inputs, **kw):
    with open(path, "wb") as f:
        f.write(render(inputs, **kw).encode("cp949"))
