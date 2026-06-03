import math

import numpy as np
from autocad.line import Line2d
from autocad.point2d import Point2d
from myalignment.geometry.simplecurve.curvegeometry import CurveGeometry
from myalignment.segment.curve_segment import CurveSegment
from myalignment.segment.segment_group.segment_group import SegmentGroup
from myalignment.segment.segment_helper import SegmentHelper
from myalignment.utils.curvedirection import CurveDirection
import matplotlib.pyplot as plt

def check_multiple_25(value, tol=0.5):
    return abs(value/25 - round(value/25)) < tol/25

def plot(sol):
    # ==========================================
    # 2. MATPLOTLIB 시각화 코드 시작
    # ==========================================
    plt.figure(figsize=(10, 8))

    # 한글 깨짐 방지 설정 (시스템 폰트에 맞게 선택 가능, 여기서는 기본 맑은고딕)
    plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False

    # 원본 기준선 (경부선 & 호남선 기본 직선)
    plt.plot([a_bp.x, a_ep.x], [a_bp.y, a_ep.y], "k--", label="경부하본선 원본")
    plt.plot([b_bp.x, b_ep.x], [b_bp.y, b_ep.y], "g--", label="호남하본선 원본")

    # 교점(PI) 및 연결선 표시
    plt.plot(
        [sol["start_pi"].x, sol["end_pi"].x],
        [sol["start_pi"].y, sol["end_pi"].y],
        color="orange",
        linestyle="-",
        linewidth=1.5,
        label="PI 연결선 (Middle Line)",
    )
    plt.scatter(
        [sol["start_pi"].x, sol["end_pi"].x],
        [sol["start_pi"].y, sol["end_pi"].y],
        color="red",
        zorder=5,
        s=50,
        label="교점 (PI)",
    )

    # 주요 선형 변곡점 추출 (BC, EC)
    s_bc, s_ec = sol["start_bc"], sol["start_ec"]
    e_bc, e_ec = sol["end_bc"], sol["end_ec"]

    #호 그리기
    start_xys = SegmentHelper.segment_to_xy(sol['start_curve'])
    end_xys = SegmentHelper.segment_to_xy(sol['end_curve'])
    x, y = zip(*start_xys)
    plt.plot(
        x ,y,
        color="red",
        linestyle="-",
        linewidth=1,
        label="시작 곡선",
    )
    x, y = zip(*end_xys)
    plt.plot(
        x, y,
        color="red",
        linestyle="-",
        linewidth=1,
        label="끝 곡선",
    )
    # 텍스트 라벨 추가
    plt.text(a_bp.x, a_bp.y, "  A_BP", fontsize=9, va="bottom")
    plt.text(b_ep.x, b_ep.y, "  B_EP", fontsize=9, va="top")
    plt.text(sol["start_pi"].x, sol["start_pi"].y, "  Start PI", color="red", weight="bold")
    plt.text(sol["end_pi"].x, sol["end_pi"].y, "  End PI", color="red", weight="bold")

    # 차트 서식 설정
    plt.title(f"철도 선형 설계 결과 시각화 (R={sol['radius']:.1f}m)", fontsize=14, pad=15)
    plt.xlabel("X 좌표 (m)", fontsize=11)
    plt.ylabel("Y 좌표 (m)", fontsize=11)
    plt.legend(loc="upper right")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.axis("equal")  # X, Y축 스케일을 1:1로 고정하여 왜곡 방지

    plt.show()
#경부하본선
a_bp = Point2d(229240.309,446972.396) #124km575
a_ep = Point2d(229391.201,446805.492) #124km800
linea = Line2d(a_bp, a_ep)
linea_angle = linea.direction  # 또는 알아내고자 하는 방향의 라디안 각도
linea_length = linea.length

#호남하본선
b_bp = Point2d(229271.098,447000.231)
b_ep = Point2d(229421.997,446833.334)
lineb = Line2d(b_bp, b_ep)

solutions = []
# 각 단계별 탈락 횟수를 기록할 딕셔너리
fail_counts = {
    "ia_filter": 0,      # 교각 제한 탈락
    "geom_create": 0,    # 곡선 생성 실패 (None 반환)
    "filter_1_bp": 0,    # 필터 1 (BP 위치 관계) 탈락
    "filter_2_dir": 0,   # 필터 2 (사이 직선 전진 방향) 탈락
    "filter_3_ep": 0,    # 필터 3 (EP 접선장 여유) 탈락
    "check_25": 0        # 25의 배수 정합(tol=0.1) 탈락
}

for j in [25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275]:
    found_for_this_j = False
    print(f">> 현재 j = {j} 탐색 중...")

    for dx in np.arange(25, int(linea_length), 0.5):
        if found_for_this_j: break

        start_pi = a_bp.moved(linea_angle, float(dx))

        for dx2 in np.arange(25, int(lineb.length), 0.5):
            end_pi = b_bp.moved(linea_angle, float(dx2))
            middle_line = Line2d(start_pi, end_pi)

            # 교각 계산 및 예각화 보정
            raw_ia = middle_line.angle_to(linea, option='rad')
            ia = abs(raw_ia)
            if ia > math.pi / 2:
                ia = math.pi - ia

            # [모니터링 0] 교각 필터
            if ia < 0.035 or ia > 0.43:
                fail_counts["ia_filter"] += 1
                continue

            radius = j / ia

            # 곡선 생성 파트
            start_curvegroup = SegmentGroup.create_from_pi(0, a_bp, start_pi, end_pi, radius, isspiral=False)
            end_curvegroup = SegmentGroup.create_from_pi(1, start_pi, end_pi, b_ep, radius, isspiral=False)

            if not start_curvegroup or not end_curvegroup:
                fail_counts["geom_create"] += 1
                continue

            start_curve = start_curvegroup.segments[0]

            end_curve = end_curvegroup.segments[0]

            # [모니터링 1] 본선 진행 방향과 start_pi 위치 관계
            vec_bp_ep = (a_ep.x - a_bp.x, a_ep.y - a_bp.y)
            vec_bp_pi = (start_pi.x - a_bp.x, start_pi.y - a_bp.y)
            if (vec_bp_ep[0] * vec_bp_pi[0] + vec_bp_ep[1] * vec_bp_pi[1]) < 0:
                fail_counts["filter_1_bp"] += 1
                continue

            # [모니터링 2] 곡선 사이 직선의 정방향 전진 체크
            ec1 = start_curvegroup.end_coord
            bc2 = end_curvegroup.start_coord
            if (vec_bp_ep[0] * (bc2.x - ec1.x) + vec_bp_ep[1] * (bc2.y - ec1.y)) <= 0:
                fail_counts["filter_2_dir"] += 1
                continue

            # [모니터링 3] end_pi와 ep 위치 관계 체크 (접선장 여유)
            end_pi_to_ep_dist = end_pi.distance_to(b_ep)
            tl = end_curve.tangent_length
            if end_pi_to_ep_dist <= tl:
                fail_counts["filter_3_ep"] += 1
                continue

            # ----------------------------------------------------
            # [★ 필터 4 추가] start_pi와 a_bp 위치 관계 체크 (위쪽 삐져남 방지)
            # ----------------------------------------------------
            start_pi_to_bp_dist = start_pi.distance_to(a_bp)
            tl_start = start_curve.tangent_length  # 시작 곡선의 접선장

            if start_pi_to_bp_dist <= tl_start:
                # 접선장보다 여유가 작으면 곡선 시점이 A_BP 위로 탈출하므로 거름
                # fail_counts 딕셔너리에 "filter_4_bp"를 추가하여 모니터링해도 좋습니다.
                continue
            # 직선 거리 정합 확인
            middle_between_curve_line = Line2d(ec1, bc2)
            straight_length = middle_between_curve_line.length

            #측점
            start_curve.start_sta = 0.0
            start_curve.end_sta = start_curve.start_sta + start_curve.length

            end_curve.start_sta = start_curve.end_sta + straight_length
            end_curve.end_sta = end_curve.start_sta + end_curve.length

            # [모니터링 4] 25m 배수 정합 탈락
            if check_multiple_25(straight_length, tol=0.1):
                solutions.append({
                    'start_pi': start_pi, 'end_pi': end_pi, 'radius': radius,
                    'start_curve_len': start_curve.length, 'straight_len': straight_length,
                    'end_curve_len': end_curve.length,
                    'start_bc': start_curvegroup.start_coord, 'start_ec': start_curvegroup.end_coord,
                    'end_bc': end_curvegroup.start_coord, 'end_ec': end_curvegroup.end_coord,
                    'start_curve': start_curve, 'end_curve': end_curve,
                })
                found_for_this_j = True
                print(f"   -> [성공] j = {j}에서 해 발견! (R={radius:.1f}m, L_straight={straight_length:.1f}m)")
                break
            else:
                fail_counts["check_25"] += 1

        if found_for_this_j: break

# 최종 탈락 리스트 리포트 출력
print("\n==================================================")
print("📊 [디버깅 통계] 왜 해가 설계 제한에 걸려 탈락했을까?")
print("--------------------------------------------------")
for filter_name, count in fail_counts.items():
    print(f" - {filter_name:<15} : {count:>6} 번 필터링됨")
print("==================================================")

# 결과 출력 및 인터랙티브 멀티 필터링 시스템
if solutions:
    # 원본 해 보존 및 현재 활성화된 필터링 해 정의
    active_solutions = solutions.copy()

    print(f"\n[성공] 초기 탐색된 총 해의 갯수: {len(solutions)}개")
    print("==================================================")
    print(" 💡 인터랙티브 선형 필터 및 시각화 명령어 안내")
    print("--------------------------------------------------")
    print(" 1) 솔루션 조회  : 번호 숫자 입력 (예: 12)")
    print(" 2) 선형길이 필터: len 최소 최대  (예: len 150 180)")
    print(" 3) 반경 필터    : r 최소 최대    (예: r 150 200)")
    print(" 4) 필터 초기화  : reset")
    print(" 5) 프로그램 종료: exit")
    print("==================================================")

    while True:
        try:
            print(f"\n[현재 필터링된 해: {len(active_solutions)}개 / 원본: {len(solutions)}개]")
            user_input = input("명령어 또는 번호 입력 >> ").strip().lower()

            # 1. 종료 처리
            if user_input == 'exit' or user_input == '-1':
                print("선형 인터랙티브 프로그램을 종료합니다.")
                break

            # 2. 필터 초기화 처리
            if user_input == 'reset':
                active_solutions = solutions.copy()
                print("[알림] 모든 필터가 초기화되어 원본 상태로 복구되었습니다.")
                continue

            # 3. 공백 기준으로 명령어 파싱 (필터링 기능)
            parts = user_input.split()

            if len(parts) >= 3:
                cmd = parts[0]
                min_val = float(parts[1])
                max_val = float(parts[2])

                # 3-1. 전체 선형 길이 필터 (len 최소 최대)
                if cmd == 'len':
                    active_solutions = [
                        s for s in solutions
                        if min_val <= (s["end_curve_len"] + s["start_curve_len"] + s["straight_len"]) <= max_val
                    ]
                    print(f"[필터 적용] 전체 선형 길이 {min_val}m ~ {max_val}m 사이의 해를 걸렀습니다.")
                    continue

                # 3-2. 반경 필터 (r 최소 최대)
                elif cmd == 'r':
                    active_solutions = [s for s in solutions if min_val <= s["radius"] <= max_val]
                    print(f"[필터 적용] 설정 반경 R {min_val}m ~ {max_val}m 사이의 해를 걸렀습니다.")
                    continue

            # 4. 단일 숫자 입력 시 -> 현재 필터링된 리스트 내에서 인덱스 조회 및 시각화
            if len(parts) == 1 and parts[0].isdigit():
                number = int(parts[0])

                if number < 0 or number >= len(active_solutions):
                    print(f"[오류] 현재 범위(0 ~ {len(active_solutions) - 1})를 벗어난 번호입니다.")
                    continue

                sol = active_solutions[number]
                total_len = sol["end_curve_len"] + sol["start_curve_len"] + sol["straight_len"]

                print(f'\n{"-" * 10} 현재 리스트의 솔루션 {number} {"-" * 10}')
                print(f'시작 PI = ({sol["start_pi"].x:.3f},{sol["start_pi"].y:.3f})')
                print(f'끝 PI = ({sol["end_pi"].x:.3f},{sol["end_pi"].y:.3f})')
                print(f'설정 반경 R = {sol["radius"]:.3f} m')
                print(f'시작 곡선 길이 = {sol["start_curve_len"]:.3f} m')
                print(f'끝 곡선 길이 = {sol["end_curve_len"]:.3f} m')
                print(f'곡선 사이 직선 길이 = {sol["straight_len"]:.3f} m')
                print(f'전체 선형 길이 = {total_len:.3f} m\n')

                # AutoCAD 커맨드 창 전용 붙여넣기 텍스트 생성
                copytext = (
                    f'_PLINE\n'  # 캐드 폴리라인 명령어 자동 실행
                    f'{a_bp.x:.3f},{a_bp.y:.3f}\n'
                    f'{sol["start_pi"].x:.3f},{sol["start_pi"].y:.3f}\n'
                    f'{sol["end_pi"].x:.3f},{sol["end_pi"].y:.3f}\n'
                    f'{b_ep.x:.3f},{b_ep.y:.3f}\n'  # 마지막에 엔터 역할을 할 공백이나 개행 필수
                    f'\n'
                )
                print(copytext)
                start_mid = sol['start_curve'].midpoint
                end_mid = sol['end_curve'].midpoint

                # AutoCAD PLINE 원호 포함 매크로 텍스트 생성
                acad_macro = (
                    f"_PLINE\n"
                    f"{a_bp.x:.4f},{a_bp.y:.4f}\n"  # 1. 출발점
                    f"{sol['start_bc'].x:.4f},{sol['start_bc'].y:.4f}\n"  # 2. 첫 곡선 시작점(BC1)까지 직선
                    f"A\n"  # 3. 원호 모드 전환
                    f"S\n"  # 4. 중간점 지정 옵션
                    f"{start_mid.x:.4f},{start_mid.y:.4f}\n"  # 5. 첫 곡선 중간점(mid) 찍기
                    f"{sol['start_ec'].x:.4f},{sol['start_ec'].y:.4f}\n"  # 6. 첫 곡선 끝점(EC1) 찍기
                    f"L\n"  # 7. 다시 직선 모드 전환
                    f"{sol['end_bc'].x:.4f},{sol['end_bc'].y:.4f}\n"  # 8. 두번째 곡선 시작점(BC2)까지 직선
                    f"A\n"  # 9. 원호 모드 전환
                    f"S\n"  # 10. 방향 지정 옵션
                    f"{end_mid.x:.4f},{end_mid.y:.4f}\n"  # 11. 끝 곡선 중간점(mid) 찍기
                    f"{sol['end_ec'].x:.4f},{sol['end_ec'].y:.4f}\n"  # 12. 두번째 곡선 끝점(EC2) 찍기
                    f"L\n"  # 13. 다시 직선 모드 전환
                    f"{b_ep.x:.4f},{b_ep.y:.4f}\n"  # 14. 종점(B_EP)까지 직선 후 종료
                    f"\n"  # 명령어 완전 종료를 위한 엔터(개행)
                )

                print("========= 아래 선을 통째로 복사해서 캐드 커맨드창에 붙여넣으세요 =========")
                print(acad_macro)
                print("========================================================================")
                # 시각화 실행 (창을 닫으면 다음 명령 대기)
                plot(sol)
                continue

            print("[오류] 올바르지 않은 명령어 형식입니다. 안내된 명령어를 확인하세요.")

        except ValueError:
            print("[오류] 수치 입력값이 잘못되었습니다. 숫자로 입력해 주세요.")
        except Exception as e:
            print(f"[오류] 예상치 못한 문제가 발생했습니다: {e}")
else:
    print("\n조건을 만족하는 해가 없어 인터랙티브 모드를 시작할 수 없습니다.")