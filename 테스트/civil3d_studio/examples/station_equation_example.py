# ==============================================================================
# 3. 실무 복합 파정(결측 + 중복) 시나리오 검증 실행 예시
# ==============================================================================
from alignment.station.equation_manager import StationEquationManager

if __name__ == "__main__":
    # 총 물리적 길이 1,000m 선형 (시점 0+000.000)
    sta_mgr = StationEquationManager(start_station=0.0, total_physical_length=1000.0)

    # 파정 1 (노선 단축 - 결측 발생): 물리적 300m 지점에서 0+300.000 = 0+350.000 (+50m 점프)
    sta_mgr.add_equation_by_back(station_back=300.0, station_ahead=350.0)

    # 파정 2 (노선 연장 - 중복 발생): 기존 체계 기준 0+700.000 지점에서 0+700.000 = 0+620.000 (-80m 겹침)
    sta_mgr.add_equation_by_back(station_back=700.0, station_ahead=620.0)

    sta_mgr.print_summary()

    # 1. 결측 구간(0+300 ~ 0+350 사이인 0+320.000) 조회 테스트
    print("\n[테스트 1] 결측 구간(0+320.000) 역산 결과:", sta_mgr.display_to_raw_all(320.0))

    # 2. 중복 구간(0+650.000) 다중 해 조회 테스트 (Zone 1과 Zone 2 두 곳에 모두 존재)
    overlap_matches = sta_mgr.display_to_raw_all(650.0)
    print("[테스트 2] 중복 구간(0+650.000) 역산 결과:")
    for raw_pos, zone_idx in overlap_matches:
        print(f"   -> Zone {zone_idx} 위치: 물리적 거리(Raw) = {raw_pos:.3f} m")

    # 3. 평면 선형(HorizontalAlignment)과의 연동 패턴 예시:
    #    - 외부 좌표(E, N) -> align.station_offset(E, N)로 raw_sta 획득 -> sta_mgr.raw_to_display(raw_sta)로 표기 측점 출력
    #    - 표기 측점(Display STA) -> sta_mgr.display_to_raw(sta, region_index)로 raw_sta 변환 -> align.point_location(raw_sta, off) 호출