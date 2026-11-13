# ==============================================================================
# 메인 테스트 실행부
# ==============================================================================
from alignment.piengine import PIAlignmentEngine
from alignment.pipoint import PIPoint

if __name__ == "__main__":
    # 실무 설계 제원 입력:
    # - IP-1은 반경 R=500m, 완화곡선 길이 L=100m 로 지정 (A값은 엔진이 자동 산출)
    # - IP-2는 반경 R=400m, 완화곡선 계수 A=180m 로 지정 (L값은 엔진이 자동 산출)
    design_pis = [
        PIPoint(name="BP",   easting=200000.000, northing=500000.000),
        PIPoint(name="IP-1", easting=200450.000, northing=500250.000, R=500.0, L=100.0),
        PIPoint(name="IP-2", easting=200950.000, northing=500100.000, R=400.0, A=180.0),
        PIPoint(name="EP",   easting=201400.000, northing=500450.000),
    ]

    # 선형 생성 실행 (시작 측점 1+000.000 = 1000.0m)
    alignment = PIAlignmentEngine(name="경부선_개량_01", pi_list=design_pis, start_station=1000.0)

    # 1. 실무 선형 계산서(IP 제원표) 자동 출력
    alignment.print_ip_report()

    # 2. 생성된 선형 위 임의 지점 정밀도 왕복 검증
    test_sta = 1485.1234567
    test_off = -14.7654321

    ge, gn = alignment.point_location(test_sta, test_off)
    calc_sta, calc_off, _, _ = alignment.station_offset(ge, gn)

    print(f"\n[정밀도 검증] 목표 측점: {test_sta:.7f} -> 역산 측점: {calc_sta:.7f} (오차: {abs(test_sta - calc_sta):.3e} m)")
    print(f"[정밀도 검증] 목표 이격: {test_off:.7f} -> 역산 이격: {calc_off:.7f} (오차: {abs(test_off - calc_off):.3e} m)")