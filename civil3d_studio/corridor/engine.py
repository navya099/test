from typing import Dict, List, Tuple, Optional

from alignment.alignment import Alignment
from alignment.widing.offset_alignment import OffsetAlignment
from profile.profile import Profile
from structure.region import StructureRegion
from superelevation.superelevation_table import SuperelevationTable
from surface.surface import ExistingGroundTerrain


class Corridor3DEngine:
    """
    수평 선형, 종단 선형, 편경사, 표준횡단(Assembly)을 결합하여
    3D 코리더 표면 및 형상선(Feature Line)을 생성하는 통합 엔진
    """

    def __init__(self,
                 name: str,
                 alignment: Alignment,
                 profile: Profile,
                 left_offset_align: OffsetAlignment,
                 right_offset_align: OffsetAlignment,
                 superelevation_table: SuperelevationTable,
                 terrain: Optional[ExistingGroundTerrain] = None,
                 structures: Optional[List[StructureRegion]] = None):
        self.name = name
        self.alignment = alignment
        self.profile = profile
        self.left_lane = left_offset_align
        self.right_lane = right_offset_align
        self.superelevation = superelevation_table
        self.terrain = terrain or ExistingGroundTerrain(base_profile_func=profile.elevation_at)
        self.structures: List[StructureRegion] = structures or []

    # ──────────────────────────────────────────────────────────
    # 구조물 관리
    # ──────────────────────────────────────────────────────────
    def add_structure(self, struct: StructureRegion):
        self.structures.append(struct)
        return self

    def get_active_structures(self, station: float) -> List[StructureRegion]:
        return [s for s in self.structures
                if s.start_station <= station <= s.end_station]

    # ──────────────────────────────────────────────────────────
    # 횡단면 샘플링 (구조물 반영)
    # ──────────────────────────────────────────────────────────
    def sample_cross_section(self, station: float) -> Dict:
        """
        특정 측점(Station)에서의 횡단면 3D 좌표 샘플링
        :return: dict {
            "station": float,
            "points": { code: (offset, e, n, el) },
            "left_mode", "right_mode": "CUT"|"FILL"|"BRIDGE"|"TUNNEL"|"WALL",
            "cut_area", "fill_area": float,
            "structures": [name, ...]
        }
        """
        # 1. 중심선 기준 2D 좌표 및 계획고
        cl_e, cl_n = self.alignment.point_location(station, 0.0)
        cl_el = self.profile.elevation_at(station)
        l_slp, r_slp = self.superelevation.get_slopes_at(station)
        l_w, _ = self.left_lane.get_offset_at(station)
        r_w, _ = self.right_lane.get_offset_at(station)
        l_w = abs(l_w)
        r_w = abs(r_w)
        # 2. 차선 끝(ETW) 및 노견 끝(Hinge)
        l_etw_off, r_etw_off = -l_w, +r_w
        l_etw_el = cl_el + l_w * l_slp
        r_etw_el = cl_el + r_w * r_slp

        l_hinge_off, r_hinge_off = l_etw_off - 1.5, r_etw_off + 1.5
        l_hinge_el = l_etw_el - 1.5 * 0.04
        r_hinge_el = r_etw_el - 1.5 * 0.04

        active_structs = self.get_active_structures(station)
        struct_types = {s.structure_type for s in active_structs}

        # 3. 구조물 유무에 따른 좌/우 끝단 처리
        if "BRIDGE" in struct_types:
            # 교량: 난간/슬래브 외측단 (폭 0.6m, 높이 +0.8m 방호벽)
            l_mode = r_mode = "BRIDGE"
            l_day_off = l_hinge_off - 0.6
            r_day_off = r_hinge_off + 0.6
            l_day_el = l_hinge_el + 0.8
            r_day_el = r_hinge_el + 0.8
        elif "TUNNEL" in struct_types:
            # 터널: 측벽 및 내공 (외측 0.8m, 상단 +4.5m)
            l_mode = r_mode = "TUNNEL"
            l_day_off = l_hinge_off - 0.8
            r_day_off = r_hinge_off + 0.8
            l_day_el = l_hinge_el + 4.5
            r_day_el = r_hinge_el + 4.5
        else:
            # 일반 토공: Daylight 자동 탐색
            l_mode, l_day_off, l_day_el = self.terrain.find_daylight_intersection(
                station, l_hinge_off, l_hinge_el, side_sign=-1.0
            )
            r_mode, r_day_off, r_day_el = self.terrain.find_daylight_intersection(
                station, r_hinge_off, r_hinge_el, side_sign=+1.0
            )

            # 옹벽 구간: Daylight 법면 → 수직 옹벽으로 대체
            for st in active_structs:
                if st.structure_type == "RETAINING_WALL":
                    if st.wall_side in ("LEFT", "BOTH"):
                        l_mode = "WALL"
                        l_day_off = l_hinge_off - 0.4
                        l_day_el = self.terrain.elevation_at(0.0, 0.0, station, l_day_off)
                    if st.wall_side in ("RIGHT", "BOTH"):
                        r_mode = "WALL"
                        r_day_off = r_hinge_off + 0.4
                        r_day_el = self.terrain.elevation_at(0.0, 0.0, station, r_day_off)

        # 4. 3D 글로벌 좌표 조립
        points_3d = {
            "L_DAY": (l_day_off, *self.alignment.point_location(station, l_day_off), l_day_el),
            "L_EPS": (l_hinge_off, *self.alignment.point_location(station, l_hinge_off), l_hinge_el),
            "L_ETW": (l_etw_off, *self.alignment.point_location(station, l_etw_off), l_etw_el),
            "CL":    (0.0, cl_e, cl_n, cl_el),
            "R_ETW": (r_etw_off, *self.alignment.point_location(station, r_etw_off), r_etw_el),
            "R_EPS": (r_hinge_off, *self.alignment.point_location(station, r_hinge_off), r_hinge_el),
            "R_DAY": (r_day_off, *self.alignment.point_location(station, r_day_off), r_day_el),
        }

        # 5. 횡단 면적 산출 (교량/터널은 토공 제외)
        cut_area, fill_area = 0.0, 0.0
        if l_mode not in ("BRIDGE", "TUNNEL") and r_mode not in ("BRIDGE", "TUNNEL"):
            ordered = [points_3d["L_DAY"], points_3d["L_EPS"], points_3d["L_ETW"],
                       points_3d["CL"], points_3d["R_ETW"], points_3d["R_EPS"], points_3d["R_DAY"]]
            for i in range(len(ordered) - 1):
                o1, _, _, z1 = ordered[i]
                o2, _, _, z2 = ordered[i + 1]
                eg1 = self.terrain.elevation_at(0.0, 0.0, station, o1)
                eg2 = self.terrain.elevation_at(0.0, 0.0, station, o2)
                avg_diff = ((z1 - eg1) + (z2 - eg2)) * 0.5
                seg_w = abs(o2 - o1)
                if avg_diff >= 0:
                    fill_area += avg_diff * seg_w
                else:
                    cut_area += abs(avg_diff) * seg_w

        return {
            "station": station,
            "points": points_3d,
            "left_mode": l_mode,
            "right_mode": r_mode,
            "cut_area": cut_area,
            "fill_area": fill_area,
            "structures": [s.name for s in active_structs]
        }

    # ──────────────────────────────────────────────────────────
    # Feature Line 추출
    # ──────────────────────────────────────────────────────────
    def extract_feature_lines(self, start_sta: float, end_sta: float,
                              interval: float = 20.0) -> Dict[str, List[Tuple[float, float, float, float]]]:
        """
        지정 측점 구간을 일정 간격으로 샘플링하여 Civil 3D Feature Line 추출
        :return: { code: [(Station, E, N, Elevation), ...] }
        """
        feature_lines: Dict[str, List[Tuple[float, float, float, float]]] = {}

        stations = []
        curr = float(start_sta)
        while curr < end_sta - 1e-6:
            stations.append(curr)
            curr += interval
        stations.append(float(end_sta))

        for sta in stations:
            sec = self.sample_cross_section(sta)
            for code, (off, e, n, el) in sec["points"].items():
                feature_lines.setdefault(code, []).append((sta, e, n, el))

        return feature_lines

    # ──────────────────────────────────────────────────────────
    # 토공량 산출 (양단면 평균법)
    # ──────────────────────────────────────────────────────────
    def compute_earthwork_volumes(self, interval: float = 20.0) -> List[Dict]:
        """
        양단면 평균법(Average End Area Method)을 이용한 전 구간 절토/성토 토공량(m³) 산출
        :return: 리포트 리스트 (각 측점별 누적 토공량)
        """
        total_len = self.alignment.total_length
        stations = []
        s = 0.0
        while s < total_len - 1e-6:
            stations.append(s)
            s += interval
        stations.append(total_len)

        report = []
        cum_cut, cum_fill = 0.0, 0.0

        # ★ 수정: stations[0] (첫 측점)을 정확히 전달
        prev_sec = self.sample_cross_section(stations[0])

        for curr_s in stations[1:]:
            curr_sec = self.sample_cross_section(curr_s)
            dist = curr_s - prev_sec["station"]

            cut_vol = (prev_sec["cut_area"] + curr_sec["cut_area"]) * 0.5 * dist
            fill_vol = (prev_sec["fill_area"] + curr_sec["fill_area"]) * 0.5 * dist
            cum_cut += cut_vol
            cum_fill += fill_vol

            report.append({
                "station": curr_s,
                "cut_area": curr_sec["cut_area"],
                "fill_area": curr_sec["fill_area"],
                "cut_vol": cut_vol,
                "fill_vol": fill_vol,
                "cum_cut": cum_cut,
                "cum_fill": cum_fill,
                "structures": curr_sec["structures"]
            })
            prev_sec = curr_sec

        # ★ 수정: return을 루프 밖으로 이동
        return report