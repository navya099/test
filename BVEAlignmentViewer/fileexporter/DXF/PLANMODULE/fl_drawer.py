from curvedirection import CurveDirection
from curvetype import CurveType
from math_utils import angle_from_center, calculate_bulge, calculate_curve_center
from model.bveroutedata import BVERouteData
from model.ipdata import IPdata
from model.segment import CurveSegment, SpiralSegment


class FLDrawer:
    def __init__(self,msp):
        self.msp = msp

    def draw_fl(self, ipdata_list: list[IPdata], bvedata: BVERouteData):
        """
        BP -> CurveSegment -> EP를 한 줄의 LWPOLYLINE으로 연결
        """
        points = []

        # 반복
        for i, ip in enumerate(ipdata_list):
            # 첫 IP는 BP
            if i == 0:
                points.append((ip.coord.x, ip.coord.y, 0))
                #첫 곡선 시작점 가져오기
                first_curve = ipdata_list[1].segment[0]
                points.append((first_curve.start_coord.x, first_curve.start_coord.y, 0))
                continue

            # IP 내부 곡선 처리
            elif i == len(ipdata_list) - 1:
                points.append((ip.coord.x, ip.coord.y, 0))
            else:
                if ip.curvetype in (CurveType.Simple, CurveType.Compound):
                    for j, seg in enumerate(ip.segment):
                        # Bulge 계산
                        start_angle = angle_from_center(seg.center_coord, seg.start_coord)
                        end_angle = angle_from_center(seg.center_coord, seg.end_coord)

                        bulge = calculate_bulge(start_angle, end_angle, ip.curve_direction)
                        # 곡선 시작점 추가
                        points.append((seg.start_coord.x, seg.start_coord.y, bulge))
                        #곡선 끝점 추가
                        points.append((seg.end_coord.x, seg.end_coord.y, 0))
                    #다음 세그먼트 직선 연결
                    if isinstance(ip, CurveSegment):
                        next_segment = ipdata_list[i + 1].segment[0]
                        points.append((next_segment.start_coord.x, next_segment.start_coord.y, 0))
                else:#완화곡선
                    for j, seg in enumerate(ip.segment):
                        if isinstance(seg, SpiralSegment):#완화곡선
                            # 완화곡선 시작점 추가
                            #points.append((seg.start_coord.x, seg.start_coord.y, 0))
                            #완화곡선구간 샘플링
                            # 곡선 샘플링 (station 기반)
                            for k, curve in enumerate(bvedata.curves[:-1]):  # 마지막은 k+1 때문에 제외
                                sta = curve.station
                                if seg.start_sta <= sta < seg.end_sta:
                                    radius = curve.radius
                                    curvedirection = CurveDirection.RIGHT if radius > 0 else CurveDirection.LEFT
                                    radius = abs(radius)
                                    next_curve = bvedata.curves[k + 1]
                                    center_coord = calculate_curve_center(
                                        curve.coord,
                                        next_curve.coord,
                                        radius,
                                        curvedirection
                                    )

                                    start_angle = angle_from_center(center_coord, curve.coord)
                                    end_angle = angle_from_center(center_coord, next_curve.coord)

                                    bulge = calculate_bulge(start_angle, end_angle, curvedirection)
                                    # bulge 값은 "다음 점으로 가는 구간"에 적용
                                    points.append((curve.coord.x, curve.coord.y, bulge))
                                    points.append((next_curve.coord.x, next_curve.coord.y, 0))  # 끝점은 항상 bulge=0
                            # 완화곡선 끝점 추가
                            #points.append((seg.end_coord.x, seg.end_coord.y, 0))

                        else:#원곡선
                            # Bulge 계산
                            start_angle = angle_from_center(seg.center_coord, seg.start_coord)
                            end_angle = angle_from_center(seg.center_coord, seg.end_coord)
                            bulge = calculate_bulge(start_angle, end_angle, ip.curve_direction)

                            # 곡선 시작점 추가
                            points.append((seg.start_coord.x, seg.start_coord.y, bulge))
                            # 곡선 끝점 추가
                            points.append((seg.end_coord.x, seg.end_coord.y, 0))
                    # 다음 세그먼트 직선 연결
                    if isinstance(ip, CurveSegment):
                        next_segment = ipdata_list[i + 1].segment[0]
                        points.append((next_segment.start_coord.x, next_segment.start_coord.y, 0))

        # LWPOLYLINE 생성
        self.msp.add_lwpolyline(points, format='xyb', dxfattribs={'layer': 'FL','color': 10})
