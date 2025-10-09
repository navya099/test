from dataclasses import field, dataclass

import folium
import numpy as np
import math
import random
import pandas as pd
from scipy.interpolate import splprep, splev

from srtm30 import SrtmDEM30

# ===== Alignment 객체 =====
@dataclass
class Alignment:
    coords: list = field(default_factory=list)
    elevations: list = field(default_factory=list)
    bridges: dict = field(default_factory=dict)  # key: segment idx, value: 튜플(start,end)
    tunnels: dict = field(default_factory=dict)
    cost: float = 0.0

    @property
    def length(self):
        return route_length(self.coords)

    @property
    def bridge_count(self):
        return len(self.bridges)
    @property
    def tunnel_count(self):
        return len(self.tunnels)

    @property
    def total_bridge_length(self):
        return sum([sum(haversine(self.coords[i], self.coords[i + 1]) for i in range(s, e))
                    for s, e in self.bridges.values()])

    @property
    def total_tunnel_length(self):
        return sum([sum(haversine(self.coords[i], self.coords[i + 1]) for i in range(s, e))
                    for s, e in self.tunnels.values()])


# ===== DEM 표고 샘플러 =====
def sample_elevations(route_coords):
    lonlat_list = [(b, a) for a, b in route_coords]
    dem = SrtmDEM30(lonlat_list)
    return dem.get_elevations()

# ===== 유틸 =====
def haversine(a, b):
    R = 6371000
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    c = 2 * math.asin(math.sqrt(math.sin(dlat / 2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon / 2)**2))
    return R * c

def route_length(coords):
    return sum(haversine(coords[i], coords[i+1]) for i in range(len(coords)-1))

# ===== 평면 경로 생성 =====
def generate_candidate(start, end, n_ctrl=3, perturb_km=5, n_samples=200):
    lats = np.linspace(start[0], end[0], n_ctrl + 2)
    lons = np.linspace(start[1], end[1], n_ctrl + 2)
    pts = [(lats[i], lons[i]) for i in range(n_ctrl+2)]
    for i in range(1, n_ctrl+1):
        ang = random.random() * 2 * math.pi
        dist = random.random() * perturb_km * 1000
        dlat = (dist * math.cos(ang)) / 111000.0
        dlon = (dist * math.sin(ang)) / (111000.0 * math.cos(math.radians(pts[i][0])+1e-6))
        pts[i] = (pts[i][0]+dlat, pts[i][1]+dlon)
    xy = np.array(pts).T
    tck, u = splprep(xy, s=0)
    u_new = np.linspace(0,1,n_samples)
    out = splev(u_new, tck)
    return list(zip(out[0], out[1]))

# ===== 종단 후보 생성 =====
def generate_longitudinal(coords, ground_elev, perturb=5):
    start_ele = ground_elev[0]
    end_ele = ground_elev[-1]
    n_ctrl = 3
    ctrl_points = np.linspace(start_ele, end_ele, n_ctrl + 2)
    for i in range(1, n_ctrl+1):
        ctrl_points[i] += random.uniform(-perturb, perturb)
    tck, u = splprep([np.arange(len(ctrl_points)), ctrl_points], s=0)
    u_new = np.linspace(0,1,len(coords))
    out = splev(u_new, tck)
    return out[1]

# ===== 종단 + 구조물 + 비용 평가 =====
def evaluate_longitudinal(coords, elevs, ground):
    dz = np.array(elevs) - np.array(ground)
    ds = np.array([haversine(coords[i], coords[i+1]) for i in range(len(coords)-1)])
    slope = np.abs(dz[:-1]/(ds + 1e-9))
    mean_slope = np.mean(slope)

    bridges, tunnels = {}, {}
    start_idx = 0
    while start_idx < len(dz)-1:
        current_sign = np.sign(dz[start_idx])
        end_idx = start_idx
        while end_idx < len(dz)-1 and np.sign(dz[end_idx]) == current_sign:
            end_idx += 1
        segment_len = ds[start_idx:end_idx].sum()
        segment_height = np.max(np.abs(dz[start_idx:end_idx]))
        if current_sign > 0 and segment_height >= 15 and segment_len >= 100:
            bridges[start_idx] = (start_idx, end_idx)
        elif current_sign < 0 and segment_height >= 15 and segment_len >= 100:
            tunnels[start_idx] = (start_idx, end_idx)
        start_idx = end_idx

    # 각 구간 길이 합산
    total_bridge_length = sum([sum(ds[s:e]) for s, e in bridges.values()])
    total_tunnel_length = sum([sum(ds[s:e]) for s, e in tunnels.values()])

    cutfill_cost = np.sum(np.abs(dz)*20.0)
    cost = route_length(coords) + 200*mean_slope + 500*total_tunnel_length + 300*total_bridge_length + 0.01*cutfill_cost

    return cost, bridges, tunnels


# ===== 후보 생성 및 평가 =====
def generate_and_rank(start, end, n_candidates=30):
    alignments = []
    for i in range(n_candidates):
        print(f"현재 회차: {i+1}")
        coords = generate_candidate(start, end, n_ctrl=random.randint(2,4))
        ground_elevs = sample_elevations(coords)
        design_elevs = generate_longitudinal(coords, ground_elevs)
        cost, bridges, tunnels = evaluate_longitudinal(coords, design_elevs, ground_elevs)

        alignment = Alignment(
            coords=coords,
            elevations=design_elevs,
            bridges=bridges,
            tunnels=tunnels,
            cost=cost
        )
        alignments.append(alignment)
    # 비용 기준 정렬
    alignments.sort(key=lambda x: x.cost)
    print("종료")
    return alignments

# ===== Folium 지도 시각화 =====
def visualize_routes(alignments, start, end, top_n=5, map_file="candidate_routes.html"):
    center = [(start[0]+end[0])/2, (start[1]+end[1])/2]
    m = folium.Map(location=center, zoom_start=7)
    colors = ['red','blue','green','orange','purple','darkred','cadetblue']

    for idx, alignment in enumerate(alignments[:top_n]):
        color = colors[idx % len(colors)]
        popup = f"ID:{idx} Cost:{alignment.cost:.1f} Bridge:{alignment.total_bridge_length:.1f}m Tunnel:{alignment.total_tunnel_length:.1f}m"
        folium.PolyLine(alignment.coords, color=color, weight=5, opacity=0.7, popup=popup).add_to(m)

    folium.Marker(location=start, popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=end, popup="End", icon=folium.Icon(color='red')).add_to(m)
    m.save(map_file)
    print(f"지도 시각화 파일({map_file})이 생성되었습니다.")

# ===== 실행 예시 =====
if __name__ == "__main__":
    start = (37.594240, 127.130699)
    end = (37.264456, 127.442329)
    alignments = generate_and_rank(start, end, n_candidates=30)

    for i, a in enumerate(alignments[:10]):
        print(f"ID:{i} Length:{a.length:.1f} Cost:{a.cost:.1f} Bridge:{a.total_bridge_length:.1f} Tunnel:{a.total_tunnel_length:.1f}")

    visualize_routes(alignments, start, end, top_n=5)
