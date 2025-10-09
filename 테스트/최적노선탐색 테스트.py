import base64
from dataclasses import field, dataclass
import io
import folium
import json
import numpy as np
import math
import random
from scipy.interpolate import splprep, splev
from srtm30 import SrtmDEM30


# ===== Alignment 객체 =====
@dataclass
class Alignment:
    coords: list = field(default_factory=list)
    elevations: list = field(default_factory=list)
    grounds: list = field(default_factory=list)
    fls: list = field(default_factory=list)
    bridges: dict = field(default_factory=dict)  # key: segment idx, value: 튜플(start,end)
    tunnels: dict = field(default_factory=dict)
    cost: float = 0.0
    radius: list = field(default_factory=list)
    grades: list = field(default_factory=list)

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

    @property
    def radius_count(self):
        return len(self.radius)

    @property
    def grades_count(self):
        return len(self.grades)

    @property
    def max_grade(self):
        return max(self.grades)

    @property
    def min_radius(self):
        return min(self.radius)


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
    c = 2 * math.asin(math.sqrt(math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2))
    return R * c


def route_length(coords):
    return sum(haversine(coords[i], coords[i + 1]) for i in range(len(coords) - 1))


# ===== 평면 경로 생성 =====
def generate_candidate(start, end, n_ctrl=3, perturb_km=5, n_samples=200):
    lats = np.linspace(start[0], end[0], n_ctrl + 2)
    lons = np.linspace(start[1], end[1], n_ctrl + 2)
    pts = [(lats[i], lons[i]) for i in range(n_ctrl + 2)]
    for i in range(1, n_ctrl + 1):
        ang = random.random() * 2 * math.pi
        dist = random.random() * perturb_km * 1000
        dlat = (dist * math.cos(ang)) / 111000.0
        dlon = (dist * math.sin(ang)) / (111000.0 * math.cos(math.radians(pts[i][0]) + 1e-6))
        pts[i] = (pts[i][0] + dlat, pts[i][1] + dlon)
    xy = np.array(pts).T
    tck, u = splprep(xy, s=0)
    u_new = np.linspace(0, 1, n_samples)
    out = splev(u_new, tck)
    return list(zip(out[0], out[1]))


def generate_longitudinal(num_points=100, min_distance=600, gl=None, chain=40):
    if gl is None:
        gl = []
    profile = generate_random_profile(num_points, min_distance, gl, chain)
    fixed_profile = check_and_adjust_elevation(profile)
    elevations = generate_station_elv(fixed_profile, gl)
    return [elevation for station, elevation in elevations], fixed_profile


def generate_station_elv(fl, gl):
    """
    계획고 지점(points) 사이를 spline 지반고를 따라 샘플링하여 선형 보간
    Args:
        fl: 계획고 주요지점 (예: [[0,110],[500,120],...])
        gl: 지반고 (예: [[0,100],[100,102],[200,103],...])
    Returns:
        station_elv: [[station, elevation], ...]
    """
    fl_stations = [s for s, _ in fl]
    fl_elevations = [e for _, e in fl]

    station_elv = []
    for sta, elev in gl:
        current_fl = np.interp(sta, fl_stations, fl_elevations)
        station_elv.append([sta, current_fl])

    return station_elv


def generate_random_profile(num_points, min_distance, gl, chain=40):
    """
    spline 기반 경로에서도 사용 가능하도록
    station 값이 정확히 일치하지 않아도 선형보간으로 지반고를 추정합니다.
    """
    # gl을 분리
    gl_stations = [s for s, _ in gl]
    gl_elevations = [e for _, e in gl]

    # 초기 설정
    start_station, start_elevation = gl[0]
    end_station, end_elevation = gl[-1]
    points = [[start_station, start_elevation + 10]]

    current_station = start_station
    current_elevation = start_elevation + 10

    for i in range(num_points - 1):
        distance_to_next = chain * math.ceil(random.uniform(min_distance, min_distance * 2) / chain)

        if current_station + distance_to_next >= end_station:
            break

        next_station = current_station + distance_to_next

        # 🔹 지반고를 선형보간으로 추정
        next_elevation = np.interp(next_station, gl_stations, gl_elevations) + 10

        current_station = next_station
        current_elevation = next_elevation
        points.append([current_station, current_elevation])

    points.append([end_station, end_elevation + 10])
    return points


def check_and_adjust_elevation(profile):
    adjusted_profile = []
    for i, (station, elevation) in enumerate(profile):
        rand_el = random.uniform(0, 20)

        if i > 0:
            prev_station, prev_elevation = adjusted_profile[-1]
            if abs(elevation - prev_elevation) > 20:
                elevation = prev_elevation + (rand_el if elevation > prev_elevation else -rand_el)
        adjusted_profile.append([station, elevation])

    return adjusted_profile


# ===== 종단 + 구조물 + 비용 평가 =====
def evaluate_longitudinal(coords, elevs, ground):
    dz = np.array(elevs) - np.array(ground)
    ds = np.array([haversine(coords[i], coords[i + 1]) for i in range(len(coords) - 1)])
    slope = np.abs(dz[:-1] / (ds + 1e-9))
    mean_slope = np.mean(slope)

    bridges, tunnels = {}, {}
    start_idx = 0
    while start_idx < len(dz) - 1:
        current_sign = np.sign(dz[start_idx])
        end_idx = start_idx
        while end_idx < len(dz) - 1 and np.sign(dz[end_idx]) == current_sign:
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

    cutfill_cost = np.sum(np.abs(dz) * 20.0)
    cost = route_length(
        coords) + 200 * mean_slope + 500 * total_tunnel_length + 300 * total_bridge_length + 0.01 * cutfill_cost

    return cost, bridges, tunnels


# ===== 후보 생성 및 평가 =====
def generate_and_rank(start, end, n_candidates=30, chain=40):
    alignments = []

    for i in range(n_candidates):
        print(f"현재 회차: {i + 1}")
        stragit_length = haversine(start, end)  # 직선길이
        n_smaples = int(stragit_length // chain)
        coords = generate_candidate(start, end, n_ctrl=random.randint(2, 4))
        ground_elevs = sample_elevations(coords)

        # 누적 거리(km) 계산
        distances = [0]
        for i in range(1, len(coords)):
            distances.append(distances[-1] + haversine(coords[i - 1], coords[i]) / 1000)  # km 단위

        gl = [(sta, ele) for sta, ele in zip(distances, ground_elevs)]
        min_distance = 1000
        max_vip = int(gl[-1][0] / min_distance)
        design_elevs, profile = generate_longitudinal(
            num_points=max_vip,
            min_distance=min_distance,
            gl=gl,
            chain=chain)

        cost, bridges, tunnels = evaluate_longitudinal(coords, design_elevs, ground_elevs)

        alignment = Alignment(
            coords=coords,
            elevations=design_elevs,
            grounds=ground_elevs,
            bridges=bridges,
            tunnels=tunnels,
            cost=cost,
            fls=profile
        )
        alignments.append(alignment)
    # 비용 기준 정렬
    alignments.sort(key=lambda x: x.cost)
    print("종료")
    return alignments


def visualize_routes_with_button(alignments, start, end, top_n=5, map_file="candidate_routes.html"):
    center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
    m = folium.Map(location=center, zoom_start=7)
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue']

    # Chart.js용 canvas
    chart_div = """
    <canvas id="profile_canvas" style="width:100%; height:300px;"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
window.profileChart = null;

function showProfile(planElevs, groundElevs, distances){
    // canvas와 실제 픽셀 크기 조정
    var canvas = document.getElementById('profile_canvas');
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;

    var ctx = canvas.getContext('2d');

    if(window.profileChart) window.profileChart.destroy();

    var planData = planElevs.map(([sta, elev]) => ({ x: sta, y: elev }));
    var groundData = groundElevs.map((e,i)=>({x: distances[i], y: e}));

    window.profileChart = new Chart(ctx,{
        type:'line',
        data:{datasets:[
            {label:'Plan', data:planData, borderColor:'red', fill:false},
            {label:'Ground', data:groundData, borderColor:'blue', fill:false}
        ]},
        options:{
            responsive:false,
            maintainAspectRatio:false,
            plugins:{legend:{display:true}},
            scales:{
                x:{
                    type:'linear',
                    position:'bottom',
                    title:{display:true, text:'Distance (km)'}
                },
                y:{
                    title:{display:true, text:'Elevation (m)'}
                }
            }
        }
    });
}
</script>

    """

    m.get_root().html.add_child(folium.Element(chart_div))

    for idx, alignment in enumerate(alignments[:top_n]):
        color = colors[idx % len(colors)]

        # elevations
        plan_elevs = [(sta / 1000, fl) for sta, fl in alignment.fls]
        ground_elevs = alignment.grounds

        # 누적 거리(km) 계산
        distances = [0]
        for i in range(1, len(alignment.coords)):
            distances.append(distances[-1] + haversine(alignment.coords[i - 1], alignment.coords[i]) / 1000)  # km 단위

        plan_json = json.dumps(plan_elevs)
        ground_json = json.dumps(ground_elevs)
        dist_json = json.dumps(distances)

        # 팝업 HTML
        popup_html = f"""
        ID: {idx} <br>
        Length:{alignment.length:.2f}
        Cost: {alignment.cost:.1f} <br>
        Bridge: {alignment.total_bridge_length:.1f}m <br>
        Tunnel: {alignment.total_tunnel_length:.1f}m <br>
        <button onclick='showProfile({plan_json}, {ground_json}, {dist_json})'>View Profile</button>
        """
        polyline = folium.PolyLine(
            locations=alignment.coords,
            color=color,
            weight=5,
            opacity=0.7,
        )
        polyline.add_child(folium.Popup(popup_html, max_width=300))
        polyline.add_to(m)

    folium.Marker(location=start, popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=end, popup="End", icon=folium.Icon(color='red')).add_to(m)

    m.save(map_file)
    print(f"지도 시각화 파일({map_file})이 생성되었습니다.")


# 종단 그래프를 base64 이미지로 변환
def plot_profile_to_base64(elevs, gound):
    from matplotlib import pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.plot(elevs, color='red')
    ax.set_xlabel("Distance")
    ax.set_ylabel("Elevation")
    ax.grid(True)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64


# ===== 실행 예시 =====
if __name__ == "__main__":
    start = (37.594240, 127.130699)
    end = (37.264456, 127.442329)
    alignments = generate_and_rank(start, end, n_candidates=30)

    for i, a in enumerate(alignments[:10]):
        print(
            f"ID:{i} Length:{a.length:.1f} Cost:{a.cost:.1f} Bridge:{a.total_bridge_length:.1f} Tunnel:{a.total_tunnel_length:.1f}")

    visualize_routes_with_button(alignments, start, end, top_n=10)
