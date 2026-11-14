import math
from typing import List, Optional, Dict, Tuple

from assembly.road import RoadAssembly
from corridor.engine import Corridor3DEngine
from profile.profile_engine import Civil3DProfileEngine
from profile.pvi import PVIPoint
from subassembly.link import SubassemblyLink
from superelevation.superelevation import SuperelevationStation
from superelevation.superelevation_table import SuperelevationTable

# 앞서 구현한 모듈들 및 클래스들 임포트 (파일 구조에 맞게 경로 조정)
# from alignment.pi_alignment import AsymmetricPIAlignmentEngine, PIPoint
# from profile.profile_engine import Civil3DProfileEngine
# from profile.pvi import PVIPoint
# from corridor.corridor_engine import Corridor3DEngine, SuperelevationTable, SuperelevationStation, RoadAssembly, SubassemblyLink


if __name__ == "__main__":
    # 1. 수평 선형(Horizontal Alignment) 구성 (예시 PI 제원)
    # (실제 환경에서는 AsymmetricPIAlignmentEngine 등을 사용하여 h_align 객체를 생성합니다)
    # design_pis = [
    #     PIPoint(name="BP", easting=200000.000, northing=500000.000),
    #     PIPoint(name="IP-1", easting=200450.000, northing=500250.000, R=500.0, L1=100.0),
    #     PIPoint(name="EP", easting=200900.000, northing=500500.000),
    # ]
    # h_align = AsymmetricPIAlignmentEngine(name="본선_수평선형", pi_list=design_pis, start_station=0.0)

    # *테스트 대상을 위한 임시 수평선형 목업(Mock) 클래스 (alignment 모듈 연동 전 테스트용)*
    class MockHorizontalAlignment:
        def point_location(self, station: float, offset: float = 0.0):
            # 단순 직선 진행 가정 (Easting 증가, Northing 일정 + 오프셋 적용)
            e = 200000.0 + station
            n = 500000.0 + offset
            return e, n


    h_align = MockHorizontalAlignment()

    # 2. 종단 선형(Vertical Profile) 구성
    pvis = [
        PVIPoint("BVP", 0.0, 40.00),
        PVIPoint("PVI-1", 450.0, 49.00, L=200.0),
        PVIPoint("EVP", 950.0, 44.00),
    ]

    # 종단 선형 엔진을 이용한 CompositeProfile 생성
    v_prof = Civil3DProfileEngine.build("본선_종단", pvis)

    # 3. 편경사 테이블 구성 (우회전 곡선 구간에서 우측 내리막 -5%, 좌측 오르막 +5% 편경사 적용)
    super_table = SuperelevationTable([
        SuperelevationStation(0.0, left_slope=-0.02, right_slope=-0.02),  # 일반 크라운 (-2% / -2%)
        SuperelevationStation(280.0, left_slope=-0.02, right_slope=-0.02),  # 편경사 완화 시작
        SuperelevationStation(380.0, left_slope=+0.05, right_slope=-0.05),  # 최대 편경사 시작 (+5% / -5%)
        SuperelevationStation(620.0, left_slope=+0.05, right_slope=-0.05),  # 최대 편경사 종료
        SuperelevationStation(700.0, left_slope=-0.02, right_slope=-0.02),  # 일반 크라운 복귀
    ])

    # 4. 표준횡단(Assembly) 구성: 편도 2차로(7.0m) + 길어깨(2.0m) + 측구/법면(1.5m)
    links = [
        SubassemblyLink(code_name="ETW", width=7.0, fixed_slope=-0.02, use_superelevation=True),  # 차선 끝 (편경사 연동)
        SubassemblyLink(code_name="EPS", width=2.0, fixed_slope=-0.04, use_superelevation=False),  # 길어깨 끝 (고정 -4%)
        SubassemblyLink(code_name="Daylight", width=1.5, fixed_slope=-0.50, use_superelevation=False),  # 비탈면 끝 (1:2 경사)
    ]
    road_assembly = RoadAssembly("왕복4차로_표준단면", left_links=links, right_links=links)

    # 5. 3D 코리더 엔진 생성 및 특정 측점 횡단 좌표 추출
    corridor = Corridor3DEngine("본선_3D코리더", h_align, v_prof, road_assembly, super_table)

    # 최대 편경사 구간 내 측점 (STA 0+450.000) 횡단 포인트 3D 좌표 출력
    target_sta = 450.0
    cross_pts = corridor.sample_cross_section(target_sta)

    print(f"\n================ [{corridor.name}] STA {target_sta:.3f}m 3D 횡단 좌표 테이블 ================")
    print(f"{'포인트 코드':<12} | {'이격(Offset)':<12} | {'Easting (X)':<15} | {'Northing (Y)':<15} | {'Elevation (Z)'}")
    print("-" * 80)

    # 좌측 끝 -> 중심선 -> 우측 끝 순서로 정렬 출력
    for code, (off, e, n, el) in sorted(cross_pts.items(), key=lambda item: item):
        print(f"{code:<12} | {off:+12.3f} | {e:15.4f} | {n:15.4f} | {el:12.4f} m")
    print("=" * 80)

    # 6. 전체 구간 50m 간격 형상선(Feature Line) 추출 예시
    flines = corridor.extract_feature_lines(start_sta=0.0, end_sta=900.0, interval=50.0)
    print(f"\n추출된 3D Feature Line 목록: {list(flines.keys())} (각 형상선당 {len(flines['CL'])}개 3D 정점 생성)")