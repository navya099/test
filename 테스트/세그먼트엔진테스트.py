#직선 세그먼트 테스트
import numpy as np

from AutoCAD.point2d import Point2d
from curvedirection import CurveDirection
from data.alignment.geometry.simplecurve.curvegeometry import CurveGeometry
from data.alignment.geometry.straight.straightgeometry import StraightGeometry
from data.segment.curve_segment import CurveSegment
from data.segment.straight_segment import StraightSegment
from matplotlib import pyplot as plt
import math

from math_utils import calculate_bearing


def test_st_segment(start_sta:float, pt,pt2,target_sta:float, isrevese=False, isoffset=False):
    """직선 세그먼트 테스트"""
    seg = StraightSegment.from_coord(start_point=pt,end_point=pt2)
    seg.start_sta = start_sta
    seg.end_sta = seg.start_sta + seg.length

    print('직선세그먼트 테스트')
    print(f'입력값 start_sta={start_sta},target_sta={target_sta}')
    #1 좌표 체크
    print(f'시작 좌표 : X={seg.start_coord.x},Y={seg.start_coord.y}')
    print(f'끝 좌표 : X={seg.end_coord.x},Y={seg.end_coord.y}')

    #2 속성 체크
    print(f'길이 : {seg.length}')
    print(f'방위각 : {seg.start_azimuth}')
    print(f'시작 측점(STA) : {seg.start_sta}')
    print(f'끝 측점(STA) : {seg.end_sta}')

    #메서드 테스트
    #distance_to_point
    ps = Point2d(218104.85745254942,434202.1723730752)
    print(f'distance_to_userpoint : {seg.distance_to_point(ps)}')
    try:
        #point_at_station
        pt,_ = seg.point_at_station(target_sta, offset=0.0)
        print(f'point_at_station STA={target_sta} : X={pt.x},Y={pt.y}')
    except ValueError as e:
        print(f'point_at_station 실패: {e}')


    try:
        station, off = seg.station_at_point(ps)
        print(f'station_at_userpoint(ps) : sta={station}, off={off}')

        resl = seg.is_contains_station(station)
        print(f'is_contains_station {station} : {resl}')

        rel = seg.is_contains_point(ps)
        print(f'is_contains_point(pt) : {rel}')

    except ValueError as e:
        print(f'station_at_point 실패: {e}')

    #reverse
    if isrevese:
        seg.reverse()
        #리버스 후 좌표 체크
        print(f'리버스 후 시작 좌표 : X={seg.start_coord.x},Y={seg.start_coord.y}')
        print(f'리버스 후 끝 좌표 : X={seg.end_coord.x},Y={seg.end_coord.y}')

        #리버스 후 속성 체크
        print(f'리버스 후 길이 : {seg.length}')
        print(f'리버스 후 방위각 : {seg.start_azimuth}')
        print(f'리버스 후 시작 측점(STA) : {seg.start_sta}')
        print(f'리버스 후 끝 측점(STA) : {seg.end_sta}')

    #create_offset
    #좌 10 offset
    if isoffset:
        seg.create_offset(offset_distance=-10)
        # 오프셋 후 좌표 체크
        print(f'오프셋 후 시작 좌표 : X={seg.start_coord.x},Y={seg.start_coord.y}')
        print(f'오프셋 후 끝 좌표 : X={seg.end_coord.x},Y={seg.end_coord.y}')

        # 오프셋 후 속성 체크
        print(f'오프셋 후 길이 : {seg.length}')
        print(f'오프셋 후 방위각 : {seg.start_azimuth}')
        print(f'오프셋 후 시작 측점(STA) : {seg.start_sta}')
        print(f'오프셋 후  끝 측점(STA) : {seg.end_sta}')

    #시각화
    fig, ax = plt.subplots()

    ax.plot(
        [seg.start_coord.x, seg.end_coord.x],[seg.start_coord.y,seg.end_coord.y],
        c='r',label='origin')
    ax.scatter(pt.x, pt.y, c='b',label='target_sta')
    ax.scatter(ps.x, ps.y, c='g',label='userpoint')
    ax.set_aspect('equal')
    ax.legend()
    plt.show()

def test_curve_segment(radius,start_angle,end_angle,direction, target_sta, start_coord, end_coord):
    seg = CurveSegment(
           _geom=CurveGeometry(radius=radius,start_azimuth=start_angle,end_azimuth=end_angle,
                               direction=direction,start_coord=start_coord,end_coord=end_coord)
    )
    seg.start_sta = 9556.468
    seg.end_sta = seg.start_sta + seg.length

    print('-단곡선 세그먼트 테스트-')
    print(f'--입력값 start_sta={seg.start_sta},target_sta={target_sta}--')
    # 1 좌표 체크
    print(f'시작 좌표 : X={seg.start_coord.x},Y={seg.start_coord.y}')
    print(f'끝 좌표 : X={seg.end_coord.x},Y={seg.end_coord.y}')
    print(f'중심 좌표 : X={seg.center_coord.x},Y={seg.center_coord.y}\n')

    # 2 속성 체크
    print('---속성 테스트---')
    print(f'길이 : {seg.length}')
    print(f'시작각도 : {seg.start_azimuth}')
    print(f'끝각도 : {seg.end_azimuth}')
    print(f'시작 측점(STA) : {seg.start_sta}')
    print(f'끝 측점(STA) : {seg.end_sta}')
    print(f'접선장 TL : {seg.tangent_length}')
    print(f'외선장 SL : {seg.external_secant}')
    print(f'중앙종거 M : {seg.middle_oridante}')
    print(f'중앙점 M : X={seg.midpoint.x},Y={seg.midpoint.y}\n')

    # 메서드 테스트
    print('ww메서드 테스트ww')
    # distance_to_point
    ps = Point2d(218451.7415  ,434440.3932 )
    print(f'임의점 PS : X={ps.x},Y={ps.y}\n')
    print(f'distance_to_userpoint : {seg.distance_to_point(ps)}')
    try:
        # point_at_station
        pt, _ = seg.point_at_station(target_sta, offset=0.0)
        print(f'point_at_station STA={target_sta} : X={pt.x},Y={pt.y}')
    except ValueError as e:
        print(f'point_at_station 실패: {e}')

    try:
        station, off = seg.station_at_point(ps)
        print(f'station_at_userpoint(ps) : sta={station}, off={off}')

        resl = seg.is_contains_station(station)
        print(f'is_contains_station {station} : {resl}')

        rel = seg.is_contains_point(ps)
        print(f'is_contains_point(pt) : {rel}')

    except ValueError as e:
        print(f'station_at_point 실패: {e}')

    # 시각화
    cx = []
    cy = []
    fig, ax = plt.subplots()
    # 곡선 전체 시각화용 샘플 생성
    xs, ys = [], []
    for s in np.linspace(seg.start_sta, seg.end_sta, 100):
        p, _ = seg.point_at_station(s)
        xs.append(p.x)
        ys.append(p.y)

    ax.plot(
        xs,ys,
        c='r', label='origin')
    ax.scatter(pt.x, pt.y, c='b', label='target_sta')
    ax.scatter(ps.x, ps.y, c='g', label='userpoint')
    ax.scatter(seg.center_coord.x, seg.center_coord.y, c='g', label='center')

    ax.set_aspect('equal')
    ax.legend()
    plt.show()
def main():

    bp = Point2d(217811.3092, 433993.7751)
    sp = Point2d(218230.7719, 434291.5622)
    bp_sta = 8900
    target_sta = 9260
    #test_st_segment(start_sta=bp_sta,pt=bp,pt2=sp, target_sta=target_sta)

    ip = Point2d(218848.2178, 434729.9024)
    # 곡선 테스트
    pc = Point2d(218348.1816, 434371.4797)
    cp = Point2d(219408.5955, 434475.9736)
    ps =Point2d(219539.3458 ,434420.5100 )
    ep =Point2d( 220748.6982, 433879.1276 )
    # 시작 , 끝 방위각 계산
    bp_azimuth = calculate_bearing(bp, sp)

    ep_azimuth = calculate_bearing(ps, ep)

    r = 1200
    target_sta = 9700
    dire = CurveDirection.RIGHT
    t1 = math.atan(142 / (2 * r))

    test_curve_segment(r, bp_azimuth - t1, ep_azimuth + t1, dire, target_sta, pc,cp)


def circle_centers_from_two_points(p1, p2, R, dirction):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    d = math.hypot(dx, dy)

    if d > 2 * R:
        raise ValueError("반지름이 너무 작음")

    mx = (p1.x + p2.x) / 2
    my = (p1.y + p2.y) / 2

    h = math.sqrt(R*R - (d/2)*(d/2))

    vx = dx / d
    vy = dy / d

    nx = -vy
    ny =  vx

    c1 = Point2d(mx + h * nx, my + h * ny)
    c2 = Point2d(mx - h * nx, my - h * ny)

    if dirction == CurveDirection.RIGHT:
        return c2
    else:
        return c1

if __name__ == '__main__':
    main()
