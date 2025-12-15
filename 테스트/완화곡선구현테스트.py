#완화곡선 테스트코드
from AutoCAD.point2d import Point2d
from data.alignment.spiral.pointcalc import SpiralPointCalculator
from data.segment.segment_group import SegmentGroup
from math_utils import calculate_bearing
from data.alignment.spiral.geometry import TransitionCurvatureCalculator
from data.alignment.spiral.params import TransitionCurveParams
import math
from matplotlib import pyplot as plt

def cal_internal_angle(bp_coordinate, ip_coordinate, ep_coordinate):
    v1 = calculate_bearing(bp_coordinate, ip_coordinate)
    v2 = calculate_bearing(ip_coordinate, ep_coordinate)
    # ±π 범위로 보정
    ia = v2 - v1
    if ia > math.pi:
        ia -= 2 * math.pi
    elif ia < -math.pi:
        ia += 2 * math.pi
    return abs(ia)

def test(bp,ip,ep,m:float,z:float,v:float,radius:float,sp_sta:float,target_sta:float):
    transition = TransitionCurveParams()
    transition.cal_params(
        m=m,
        z=z,
        v=v,
        radius=radius,
        internal_angle=cal_internal_angle(bp, ip, ep),
        sp_type=None
    )
    group = SegmentGroup.create_from_pi(
        group_id=0,
        bp=bp,
        ip=ip,
        ep=ep,
        radius=radius,
        isspiral=True,
        transition=transition
    )

    # 곡선 세그먼트 (IP)
    bp_azimuth = calculate_bearing(group.bp_coordinate, group.ip_coordinate)
    ep_azimuth = calculate_bearing(group.ip_coordinate, group.ep_coordinate)

    # 좌표계산 호출
    cal = TransitionCurvatureCalculator(
        tr_params=transition,
        h1=bp_azimuth,
        h2=ep_azimuth,
        ip=group.ip_coordinate,
        direction=group.curve_direction
    )
    cal.run()


    #완화곡선 측점계산
    #SP~PC
    sp_curve = group.segments[0]
    sp_curve.start_sta = sp_sta
    sp_curve.end_sta = sp_curve.start_sta + sp_curve.length

    #PC~CP
    pc_curve = group.segments[1]
    pc_curve.start_sta = sp_curve.end_sta
    pc_curve.end_sta = pc_curve.start_sta + pc_curve.length

    #CP~PS
    ps_curve = group.segments[-1]
    ps_curve.start_sta = pc_curve.end_sta
    ps_curve.end_sta = ps_curve.start_sta + ps_curve.length

    # 임의의 지점에 대한 좌표 및 방위각
    pt,dr = None ,None
    for curve in (sp_curve, pc_curve, ps_curve):
        if curve.start_sta < target_sta < curve.end_sta:
            pt, dr = curve.point_at_station(target_sta)
            break
    if pt is None:
        raise ValueError(f"Station {target_sta}이(가) 어느 커브에도 속하지 않음")

    # 곡선 전체 시각화용 샘플 생성
    xs, ys = [], []
    for s in range(int(sp_sta), int(ps_curve.end_sta), 20):
        for curve in (sp_curve, pc_curve, ps_curve):
            if curve.start_sta <= s <= curve.end_sta:
                p, _ = curve.point_at_station(s)
                xs.append(p.x)
                ys.append(p.y)
                break

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)
    ax.plot(xs, ys)

    print('\n완화곡선 제원출력\n')
    print(f'방위각1={90 - math.degrees(group.bp_azimuth)}')
    print(f'방위각2={90 - math.degrees(group.ep_azimuth)}')
    print(f'교각={math.degrees(group.internal_angle)}')
    print(f'X1={transition.x1}')
    print(f'Y1={transition.y1}')
    print(f'접선각 θ={math.degrees(transition.theta_pc)}')
    print(f'원곡선교각 ia={math.degrees(transition.circle_internal_angle)}')
    print(f'이정량 F={transition.f}')
    print(f'수평좌표차 K={transition.k}')
    print(f'원곡선장 CL={transition.circle_length}')
    print(f'완화곡선장 L={transition.l}')
    print(f'X2={transition.x2}')
    print(f'접선장 TL={transition.total_tangent_length}')
    print(f'곡선장 CL={transition.total_curve_length}')
    print('\n완화곡선 측점출력\n')
    print(f'SP={sp_curve.start_sta}')
    print(f'PC={pc_curve.start_sta}')
    print(f'CP={pc_curve.end_sta}')
    print(f'PS={ps_curve.end_sta}')
    print('\n완화곡선 좌표출력\n')
    print(f'SP={cal.start_transition.x},{cal.start_transition.y}')
    print(f'PC={cal.start_circle.x},{cal.start_circle.y}')
    print(f'CP={cal.end_circle.x},{cal.end_circle.y}')
    print(f'PS={cal.end_transition.x},{cal.end_transition.y}')
    print(f'\n임의 지점 {target_sta}의 좌표 및 접선 방위각=\nX={pt.x},Y={pt.y}, DR={90 - math.degrees(dr)}')

    plt.show()
bp=Point2d(217366.8274,433678.2264)
ip=Point2d(218848.2178, 434729.9024)
ep=Point2d(220748.6982,433879.1276)
m=1000
z=0.142
v=120
radius=1200
sp_sta = 9414.4184
target_sta = 9420
test(
    bp=bp,
    ip=ip,
    ep=ep,
    m=m,
    z=z,
    v=v,
    radius=radius,
    sp_sta=sp_sta,
    target_sta=target_sta
)
