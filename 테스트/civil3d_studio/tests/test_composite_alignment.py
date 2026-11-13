import math

from alignment.alignment import CompositeAlignment

# 철도/도로 표준 복합 선형 구성:
# [직선 150m] -> [진입 완화곡선 80m] -> [원곡선 R=400m, L=120m] -> [진출 완화곡선 80m] -> [직선 200m]
align = CompositeAlignment(
    name="KRS_Line_01",
    start_easting=204500.000,
    start_northing=541200.000,
    start_angle_rad=math.radians(30.0),
    start_station=1000.0  # 시작 측점 1+000.000
    )

align.add_line(length=150.0)                                                    # STA 1000 ~ 1150 (직선)
align.add_japanese_cubic_spiral(R=400.0, L=80.0, turn_direction=-1, is_exit_spiral=False) # STA 1150 ~ 1230 (진입 완화)
align.add_arc(R=400.0, length=120.0, turn_direction=-1)                         # STA 1230 ~ 1350 (우회전 원곡선)
align.add_japanese_cubic_spiral(R=400.0, L=80.0, turn_direction=-1, is_exit_spiral=True)  # STA 1350 ~ 1430 (진출 완화)
align.add_line(length=200.0)                                                    # STA 1430 ~ 1630 (직선)

print(f"선형 이름: {align.name} | 전체 측점 범위: {align.starting_station:.3f} ~ {align.ending_station:.3f} m\n")
# 각 구간(직선, 진입완화, 원곡선, 진출완화, 종점직선)을 모두 관통하는 검증 샘플
test_samples = [
(1075.500,  12.500, "1구간: 시점 직선"),
(1192.345, -18.750, "2구간: 진입 일본3차포물선"),
(1290.123,  25.000, "3구간: 중앙 원곡선"),
(1388.888, -10.250, "4구간: 진출 일본3차포물선"),
(1520.000,   0.000, "5구간: 종점 직선 중심선"),
]
for target_sta, target_off, label in test_samples:
    # 1. 정방향 계산 (Station, Offset -> Easting, Northing)
    ge, gn = align.point_location(target_sta, target_off)
    # 2. 역방향 계산 (Easting, Northing -> Station, Offset)
    calc_sta, calc_off, _, _ = align.station_offset(ge, gn)
    sta_err = abs(target_sta - calc_sta)
    off_err = abs(target_off - calc_off)
    print(f"[{label:<16}] STA 오차: {sta_err:.3e} m | OFF 오차: {off_err:.3e} m")