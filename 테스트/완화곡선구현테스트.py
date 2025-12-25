#완화곡선 테스트코드
from AutoCAD.point2d import Point2d
from data.alignment.geometry.spiral.params import TransitionCurveParams
from data.alignment.transition.calulator import TransitionCalulator
from data.segment.segment_group.segment_group import SegmentGroup
from math_utils import calculate_bearing
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
    ia = cal_internal_angle(bp, ip, ep)

    transition = TransitionCurveParams(m=m,
        z=z,
        v=v,
        radius=radius,
        internal_angle=ia,
        sp_type=None
    )
    transition.cal_params()

    group = SegmentGroup.create_from_pi(
        group_id=1,
        bp=bp,
        ip=ip,
        ep=ep,
        radius=radius,
        isspiral=True,
        transition1=transition,
        transition2=transition
    )

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

    # 접선장 및 CL계산
    d1, d2, delta, lc = TransitionCalulator.cal_spec(radius, transition, transition, ia)

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
    for s in range(int(sp_sta), int(ps_curve.end_sta), 40):
        for curve in (sp_curve, pc_curve, ps_curve):
            if curve.start_sta <= s <= curve.end_sta:
                p, _ = curve.point_at_station(s)
                xs.append(p.x)
                ys.append(p.y)
                break

    print('\n완화곡선 제원출력\n')
    print(f'방위각1={90 - math.degrees(group.bp_azimuth)}')
    print(f'방위각2={90 - math.degrees(group.ep_azimuth)}')
    print(f'교각={math.degrees(group.internal_angle)}')
    print(f'X1={transition.x1}')
    print(f'Y1={transition.y1}')
    print(f'접선각 θ={math.degrees(transition.theta_pc)}')
    print(f'원곡선교각 ia={math.degrees(pc_curve.delta)}')
    print(f'이정량 F={transition.f}')
    print(f'수평좌표차 K={transition.k}')
    print(f'원곡선장 CL={pc_curve.length}')
    print(f'완화곡선장 L={transition.l}')
    print(f'X2={transition.x2}')
    print(f'접선장 TL={d1}')
    print(f'곡선장 CL={sp_curve.length + pc_curve.length + ps_curve.length}')
    print('\n완화곡선 측점출력\n')
    print(f'SP={sp_curve.start_sta}')
    print(f'PC={pc_curve.start_sta}')
    print(f'CP={pc_curve.end_sta}')
    print(f'PS={ps_curve.end_sta}')
    print('\n완화곡선 좌표출력\n')
    print(f'SP={sp_curve.start_coord.x},{sp_curve.start_coord.y}')
    print(f'PC={sp_curve.end_coord.x},{sp_curve.end_coord.y}')
    print(f'CP={ps_curve.start_coord.x},{ps_curve.start_coord.y}')
    print(f'PS={ps_curve.end_coord.x},{ps_curve.end_coord.y}')
    print(f'\n임의 지점 {target_sta}의 좌표 및 접선 방위각=\nX={pt.x},Y={pt.y}, DR={90 - math.degrees(dr)}')

    fig, ax = plt.subplots()
    ax.scatter(sp_curve.start_coord.x, sp_curve.start_coord.y, c='b')
    ax.scatter(pc_curve.start_coord.x, pc_curve.start_coord.y, c='b')
    ax.scatter(ps_curve.start_coord.x, ps_curve.start_coord.y, c='b')
    ax.scatter(ps_curve.end_coord.x, ps_curve.end_coord.y, c='b')
    ax.scatter(pt.x, pt.y, c='r', marker='x')

    ax.scatter(ip.x, ip.y, c='g')
    ax.plot(
        [bp.x, ip.x, ep.x],
        [bp.y, ip.y, ep.y],
        c='b'
    )
    curve_plot, = ax.plot(xs, ys, color='red')
    ax.set_aspect('equal')
    plt.show()

bp=Point2d(217366.8274,433678.2264)
ip=Point2d(218848.2178, 434729.9024)
ep=Point2d(220748.6982,433879.1276)
m=1000
z=0.142
v=120
radius=1200
sp_sta = 9414.4184
target_sta = 10760
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
