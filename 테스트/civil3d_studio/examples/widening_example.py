# ==============================================================================
# 3. 통합 실행 예시 (모선형 + 우측 버스베이 확폭 + 좌측 가감속차선 확폭)
# ==============================================================================
from alignment.alignment import Alignment
from alignment.pipoint import PIPoint
from alignment.widing.offset_alignment import OffsetAlignment
from alignment.widing.wideing_region import WideningRegion

if __name__ == "__main__":
    # 앞서 작성한 HorizontalAlignment가 동일 모듈/패키지에 있다고 가정하고 최소 코어 임포트

    # 1. 상위 모선형(Parent Alignment) 생성 (총 연장 약 1,038m)
    pis = [
        PIPoint("BP",   200000.000, 500000.000),
        PIPoint("IP-1", 200500.000, 500250.000, R=500.0, L1=100.0, L2=80.0),
        PIPoint("EP",   201050.000, 500050.000),
    ]
    parent_align = Alignment.create("본선_중심선", pis, start_station=0.0)

    # 2. 우측 Offset Alignment 생성 (기본 차선폭 +3.5m) + 버스 정차대(Bus Bay) 확폭 추가
    right_etw = OffsetAlignment(
        name="우측_차선끝_ETW",
        parent_alignment=parent_align,
        nominal_offset=+3.5
    )
    right_etw.add_widening(
        WideningRegion(
            name="버스정차대_확폭",
            start_station=150.0,
            end_station=270.0,
            widening_width=3.0,          # +3.5m -> +6.5m 로 3.0m 확폭
            entry_transition_len=30.0,   # STA 150 ~ 180 진입 테이퍼
            exit_transition_len=25.0,    # STA 245 ~ 270 복귀 테이퍼
            transition_type="Smooth"     # S자 곡선 테이퍼 적용
        )
    )

    # 3. 좌측 Offset Alignment 생성 (기본 차선폭 -3.5m) + 교차로 좌회전 감속차선 확폭 추가
    left_etw = OffsetAlignment(
        name="좌측_차선끝_ETW",
        parent_alignment=parent_align,
        nominal_offset=-3.5
    )
    left_etw.add_widening(
        WideningRegion(
            name="교차로_감속차선",
            start_station=600.0,
            end_station=850.0,
            widening_width=3.25,         # -3.5m -> -6.75m 로 좌측 바깥쪽 확폭
            entry_transition_len=60.0,   # STA 600 ~ 660 직선 테이퍼
            exit_transition_len=40.0,    # STA 810 ~ 850 직선 테이퍼
            transition_type="Linear"
        )
    )

    # 4. 측점별 동적 폭원 및 글로벌 좌표 변화 확인 출력
    print(f"\n================ [{right_etw.name}] 확폭 구간 동적 좌표 테이블 ================")
    print(f"{'모선형 측점(STA)':<15} | {'이격 거리(m)':<13} | {'폭원 변화율':<11} | {'Easting (X)':<15} | {'Northing (Y)'}")
    print("-" * 82)
    for sta in [140.0, 150.0, 165.0, 180.0, 210.0, 245.0, 257.5, 270.0, 300.0]:
        off_w, slope = right_etw.get_offset_at(sta)
        ge, gn = right_etw.point_location(sta)
        print(f"{sta:15.3f} | {off_w:+13.4f} | {slope:+11.4f} | {ge:15.4f} | {gn:15.4f}")
    print("=" * 82)