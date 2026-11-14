from typing import Dict, List, Tuple


class Corridor3DEngine:
    """
    수평 선형, 종단 선형, 편경사, 표준횡단(Assembly)을 결합하여
    3D 코리더 표면 및 형상선(Feature Line)을 생성하는 통합 엔진
    """

    def __init__(self, name: str, alignment, profile, assembly, superelevation_table):
        self.name = name
        self.alignment = alignment  # 수평 선형 객체 (Horizontal Alignment)
        self.profile = profile  # 종단 선형 객체 (Vertical Profile / CompositeProfile)
        self.assembly = assembly  # 도로 표준횡단 객체 (RoadAssembly)
        self.superelevation = superelevation_table  # 편경사 관리자 (SuperelevationTable)

    def sample_cross_section(self, station: float) -> Dict[str, Tuple[float, float, float, float]]:
        """
        특정 측점(Station)에서의 횡단면 3D 좌표 샘플링
        :return: { 포인트코드: (Offset, Easting, Northing, Elevation) } 딕셔너리
        """
        # 1. 중심선(Crown / Centerline) 기준 2D 좌표 및 계획고(EL) 산출
        cl_e, cl_n = self.alignment.point_location(station, 0.0)
        cl_el, _ = self.profile.elevation_and_grade_at(station)

        # 2. 해당 측점의 좌/우 편경사 값 취득
        left_super, right_super = self.superelevation.get_slopes_at(station)

        section_points: Dict[str, Tuple[float, float, float, float]] = {
            "CL": (0.0, cl_e, cl_n, cl_el)
        }

        # 3. 좌측(Left, Offset < 0) 서브어셈블리 순차 계산
        curr_off = 0.0
        curr_el = cl_el
        for link in self.assembly.left_links:
            slope = left_super if link.use_superelevation else link.fixed_slope
            curr_off -= link.width
            curr_el += link.width * slope
            ge, gn = self.alignment.point_location(station, curr_off)
            section_points[f"L_{link.code_name}"] = (curr_off, ge, gn, curr_el)

        # 4. 우측(Right, Offset > 0) 서브어셈블리 순차 계산
        curr_off = 0.0
        curr_el = cl_el
        for link in self.assembly.right_links:
            slope = right_super if link.use_superelevation else link.fixed_slope
            curr_off += link.width
            curr_el += link.width * slope
            ge, gn = self.alignment.point_location(station, curr_off)
            section_points[f"R_{link.code_name}"] = (curr_off, ge, gn, curr_el)

        return section_points

    def extract_feature_lines(self, start_sta: float, end_sta: float, interval: float = 20.0) -> Dict[
        str, List[Tuple[float, float, float, float]]]:
        """
        지정 측점 구간을 일정 간격(Frequency)으로 샘플링하여 Civil 3D Feature Line(3D 형상선) 추출
        :return: { 포인트코드: [(Station, Easting, Northing, Elevation), ...] }
        """
        feature_lines: Dict[str, List[Tuple[float, float, float, float]]] = {}

        # 샘플링 측점 리스트 생성 (종점 측점 반드시 포함)
        stations = []
        curr = float(start_sta)
        while curr < end_sta - 1e-6:
            stations.append(curr)
            curr += interval
        stations.append(float(end_sta))

        for sta in stations:
            sec = self.sample_cross_section(sta)
            for code, (off, e, n, el) in sec.items():
                if code not in feature_lines:
                    feature_lines[code] = []
                feature_lines[code].append((sta, e, n, el))

        return feature_lines