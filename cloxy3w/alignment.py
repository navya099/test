"""
alignment.py - 좌표(BP, IP1..IPn, EP)에서 방위각·교각·IP 측점을 계산해
ip2_engine 의 입력(IP2Input)을 만들어 주는 앞단 모듈.

좌표 규약(원본 DAT 와 동일): X = 북(N), Y = 동(E), 방위각은 +X(북)에서 시계방향.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from ip2_engine import IP2Input, solve_curve


@dataclass
class Vertex:
    name: str                 # "BP", "IP1", ..., "EP"
    x: float
    y: float
    R: float = 0.0
    B: float = 2.2
    A2: float = 0.0           # A"
    D: float = 4.4
    L: float = 0.0


def azimuth(p: Vertex, q: Vertex) -> float:
    """p -> q 방위각(십진 도, 0~360)"""
    return math.degrees(math.atan2(q.y - p.y, q.x - p.x)) % 360.0


def distance(p: Vertex, q: Vertex) -> float:
    return math.hypot(q.x - p.x, q.y - p.y)


def deflection(az_in: float, az_out: float):
    """(교각 IA 십진 도, 좌회전 여부)  ─ 방위각이 감소하면 좌회전"""
    d = (az_in - az_out) % 360.0
    left = d < 180.0
    return (d if left else 360.0 - d), left


@dataclass
class Project:
    vertices: list                        # BP, IP..., EP
    start_station: float = 0.0            # BP 의 측점
    chain: float = 20.0                   # 측점 간격
    warnings: list = field(default_factory=list)

    @property
    def ips(self):
        return self.vertices[1:-1]


def build_inputs(prj: Project, sta_ranges=None):
    """Project -> list[IP2Input].  반환: (inputs, 계산 요약 list[dict])"""
    v = prj.vertices
    n = len(v) - 2
    if n < 1:
        raise ValueError("BP, EP 사이에 IP 가 최소 1개 필요합니다")
    az = [azimuth(v[i], v[i + 1]) for i in range(len(v) - 1)]   # 구간 방위각 (n+1 개)
    out, info = [], []
    sta_ip_prev = None
    for k in range(1, n + 1):
        ip = v[k]
        ia, left = deflection(az[k - 1], az[k])
        if ip.R <= 0:
            raise ValueError(f"{ip.name}: 반경 R 이 필요합니다")
        TL = ip.R * math.tan(math.radians(ia) / 2)
        CL = ip.R * math.radians(ia)
        if k == 1:
            sta = prj.start_station + distance(v[0], ip)
        else:
            p = v[k - 1]
            ia_p, _ = deflection(az[k - 2], az[k - 1])
            TLp = p.R * math.tan(math.radians(ia_p) / 2)
            CLp = p.R * math.radians(ia_p)
            sta = sta_ip_prev - TLp + CLp + distance(p, ip) - TLp
            if TLp + TL > distance(p, ip):
                prj.warnings.append(f"{p.name}-{ip.name}: 두 곡선의 접선장 합이 구간 길이를 넘습니다")
        sta_ip_prev = sta
        if ia < 1e-9:
            prj.warnings.append(f"{ip.name}: 교각이 0 입니다")
        if abs(ip.D - 2 * ip.B) > 1e-9:
            prj.warnings.append(f"{ip.name}: D≠2B — 원본과 대조되지 않은 조건입니다")
        item = IP2Input(k, ip.R, ip.L, ip.B, ip.A2, ip.D, sta, ia, 0.0, 0.0, prj.chain,
                        "Y", ip.x, ip.y, az[k - 1], az[k])
        if sta_ranges:
            item.sta_start, item.sta_end = sta_ranges[k - 1]
        else:                                    # 곡선 전체(BTC~ETC)를 chain 배수로 감싸는 범위를 자동 결정
            cv0 = solve_curve(item)
            lo = min(l.BTC for l in cv0.lines.values()); hi = max(l.ETC for l in cv0.lines.values())
            item.sta_start = math.floor(lo / prj.chain) * prj.chain
            item.sta_end = math.ceil(hi / prj.chain) * prj.chain
        out.append(item)
        info.append(dict(name=ip.name, sta=sta, ia=ia, left=left, az_in=az[k - 1], az_out=az[k],
                         TL=TL, CL=CL))
    return out, info


# ----------------------------------------------------------------- 파일 입출력
def read_xy_txt(path: str):
    """헤더 없는 'X,Y' TXT (구분자: 쉼표/공백/탭/세미콜론, 빈 줄·BOM 허용) -> [(x, y)]"""
    import re
    pts = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith(("#", "//")):
                continue
            parts = [t for t in re.split(r"[,\s;]+", ln) if t]
            if len(parts) < 2:
                raise ValueError(f"좌표를 읽을 수 없는 줄: {ln!r}")
            pts.append((float(parts[0]), float(parts[1])))
    return pts


def project_from_points(points, params, start_station=0.0, chain=20.0) -> "Project":
    """points[0]=BP, points[-1]=EP, 가운데는 IP.  params: IP 별 dict(R,B,A2,D,L) 리스트(IP 순서)"""
    if len(points) - 2 != len(params):
        raise ValueError(f"IP 개수({len(points) - 2})와 파라미터 개수({len(params)})가 다릅니다")
    v = [Vertex("BP", *points[0])]
    for i, (pt, pr) in enumerate(zip(points[1:-1], params), 1):
        v.append(Vertex(f"IP{i}", pt[0], pt[1], pr["R"], pr.get("B", 2.2), pr.get("A2", 0.0),
                        pr.get("D", 4.4), pr.get("L", 0.0)))
    v.append(Vertex("EP", *points[-1]))
    return Project(v, start_station, chain)


def deg_to_packed(deg: float) -> float:
    """십진 도 -> DDD.MMSSss (0.01초 단위, 원본 DAT 의 IA 표기)"""
    tot = round(deg * 3600 * 100)            # 0.01초
    d, rem = divmod(tot, 360000)
    m, ss = divmod(rem, 6000)
    return float(f"{d}.{m:02d}{ss // 100:02d}{ss % 100:02d}00")


def write_dat(path: str, inputs) -> None:
    """원본 CLOXY 가 읽는 DAT 로 내보내기 (교차 검증/프로젝트 보관용)"""
    L = [f"{len(inputs):3d}"]
    for i in inputs:
        L.append(f"{i.ip_no:5d}{i.R:12.4f}{i.L:12.4f}{i.B:11.4f}{i.A2:11.4f}{i.D:11.4f}")
        L.append(f"{i.ip_sta:14.6f}{deg_to_packed(i.ia_deg):17.8f}")
        L.append(f"{i.sta_start:14.6f}{i.sta_end:14.6f}{i.sta_step:13.6f}")
        L.append("y" if i.ip_n is not None else "n")
        if i.ip_n is not None:
            L.append(f"{i.ip_n:16.6f}{i.ip_e:16.6f}{i.az_in_deg:18.9f}{i.az_out_deg:18.9f}")
    with open(path, "w", encoding="cp949", newline="") as f:
        f.write("\r\n".join(L) + "\r\n")
