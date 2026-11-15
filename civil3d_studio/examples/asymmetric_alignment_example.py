# 실무 복합 사례:
# - IP-1: 비대칭 완화곡선 (R=500m, 진입 L1=110m, 진출 L2=70m)
# - IP-2: 비대칭 파라미터 입력 (R=400m, 진입 A1=200m -> L1=100m, 진출 A2=160m -> L2=64m)
# - IP-3: 단측 완화곡선 (R=600m, 진입 L1=90m, 진출 L2=0m)
import math

from alignment.piengine import PIAlignmentEngine
from alignment.pipoint import PIPoint

design_pis = [
PIPoint(name="BP",   easting=200000.000, northing=500000.000),
PIPoint(name="IP-1", easting=200500.000, northing=500250.000, R=500.0, L1=110.0, L2=70.0),
PIPoint(name="IP-2", easting=201050.000, northing=500050.000, R=400.0, A1=200.0, A2=160.0),
PIPoint(name="IP-3", easting=201550.000, northing=500300.000, R=600.0, L1=90.0,  L2=0.0),
PIPoint(name="EP",   easting=202000.000, northing=500200.000),
]

align = PIAlignmentEngine(name="비대칭_통합선형_01", pi_list=design_pis, start_station=0.0)
align.print_ip_report()

# 기하 연속성 검증: 종점(EP) 좌표가 마지막 직선 요소의 끝점과 오차 없이 일치하는지 확인
last_end_e, last_end_n, _, end_sta = align.entities[-1].end_pose
ep = design_pis[-1]
ep_err = math.hypot(last_end_e - ep.easting, last_end_n - ep.northing)
print(f"\n[기하 연속성 검증] 계산된 최종 종점 좌표와 설계 EP 좌표 오차: {ep_err:.3e} m")

# 비대칭 진입/진출 완화곡선 내부 구간 왕복 정밀도 테스트
for sta in [380.1234567, 510.7654321, 960.1111111, 1490.9876543]:
    ge, gn = align.point_location(sta, offset=12.3456789)
    c_sta, c_off, _, _ = align.station_offset(ge, gn)
    print(f"STA {sta:10.4f} -> 역산 오차: STA={abs(sta - c_sta):.3e} m, OFF={abs(12.3456789 - c_off):.3e} m")