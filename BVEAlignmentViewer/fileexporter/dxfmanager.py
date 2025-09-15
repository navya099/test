import ezdxf

from core.calculator import Calculator
from math_utils import angle_from_center
from model.model import IPdata, CurveType, CurveDirection, CurveSegment, SpiralSegment, BVERouteData
from utils import try_parse_int
import math

class DXFController:
    def __init__(self):
        self.msp = None
        self.doc = None

    def export_dxf(self, ipdata: list[IPdata], bvedata: BVERouteData ,filepath: str):
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()

        # IP라인 그리기
        self._draw_ipline(ipdata)

        #FL 그리기
        self._draw_fl(ipdata ,bvedata)

        # IP문자
        self._draw_texts(ipdata, 'IP문자',
                         lambda ip, i, n: 'BP' if i == 0 else 'EP' if i == n - 1 else f'IP{ip.ipno}' if try_parse_int(
                             ip.ipno) else str(ip.ipno))

        # R문자
        self._draw_mtexts(ipdata, 'R문자',
                         lambda ip, i, n: None if i == 0 or i == n - 1 else f'\nR={ip.radius:.2f}' if isinstance(
                             ip.radius, float) else f'\nR1={ip.radius[0]:.2f}\nR2={ip.radius[1]:.2f}')

        #저장
        self.doc.saveas(filepath)

    def _draw_ipline(self, ipdata: list[IPdata]):
        points = [(ip.coord.x, ip.coord.y) for ip in ipdata]
        lwpolyline = self.msp.add_lwpolyline(points, dxfattribs={'layer': 'IP라인'})

    def _draw_texts(self, ipdata_list: list[IPdata], layer: str, text_func):
        """
        텍스트 추가용 공통 메소드
        Args:
            ipdata_list: IPdata 리스트
            layer: 문자열, 레이어 이름
            text_func: 각 IPdata에 대해 문자열 반환 함수
        """
        for i, ip in enumerate(ipdata_list):
            text = text_func(ip, i, len(ipdata_list))
            if text:
                self.msp.add_text(text, dxfattribs={
                    'insert': (ip.coord.x, ip.coord.y),
                    'height': 5,
                    'color': 1,
                    'layer': layer
                })

    def _draw_mtexts(self, ipdata_list: list[IPdata], layer: str, text_func):
        """
        텍스트 추가용 공통 메소드
        Args:
            ipdata_list: IPdata 리스트
            layer: 문자열, 레이어 이름
            text_func: 각 IPdata에 대해 문자열 반환 함수
        """
        for i, ip in enumerate(ipdata_list):
            text = text_func(ip, i, len(ipdata_list))
            if text:
                self.msp.add_mtext(text, dxfattribs={
                    'insert': (ip.coord.x, ip.coord.y),
                    'char_height': 5,
                    'color': 1,
                    'layer': layer
                })
    def _draw_fl(self, ipdata_list: list[IPdata], bvedata: BVERouteData):
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
                if ip.curvetype in (CurveType.Simple, CurveType.Complex):
                    for j, seg in enumerate(ip.segment):
                        # Bulge 계산
                        start_angle = angle_from_center(seg.center_coord, seg.start_coord)
                        end_angle = angle_from_center(seg.center_coord, seg.end_coord)
                        # LEFT: 반시계 +, RIGHT: 시계 -
                        if ip.curve_direction == CurveDirection.LEFT:
                            sweep = (end_angle - start_angle + 360) % 360
                        else:
                            sweep = (start_angle - end_angle + 360) % 360
                            sweep = -sweep  # Bulge 정의상 음수

                        bulge = math.tan(math.radians(sweep / 4))
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
                            points.append((seg.start_coord.x, seg.start_coord.y, 0))
                            #완화곡선구간 샘플링
                            for i, coord in enumerate(bvedata.coords):
                                sta = bvedata.firstblock + i * bvedata.block_interval
                                if seg.start_sta < sta < seg.end_sta:
                                    points.append((coord.x, coord.y, 0))

                            # 완화곡선 끝점 추가
                            points.append((seg.end_coord.x, seg.end_coord.y, 0))

                        else:#원곡선
                            # Bulge 계산
                            start_angle = angle_from_center(seg.center_coord, seg.start_coord)
                            end_angle = angle_from_center(seg.center_coord, seg.end_coord)
                            # LEFT: 반시계 +, RIGHT: 시계 -
                            if ip.curve_direction == CurveDirection.LEFT:
                                sweep = (end_angle - start_angle + 360) % 360
                            else:
                                sweep = (start_angle - end_angle + 360) % 360
                                sweep = -sweep  # Bulge 정의상 음수

                            bulge = math.tan(math.radians(sweep / 4))
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

    def _draw_arc(self, ip: IPdata):
        """
        ipdata를 바탕으로 호 객체를 그리는 메소드
        Args:
            ip:
        Returns:
            msp.arc
        """

        #ip내부 호 객체 요소 추출
        if ip.curvetype in (CurveType.Simple, CurveType.Complex):
            for seg in ip.segment:
                center = seg.center_coord
                start = seg.start_coord
                end = seg.end_coord
                r = seg.radius

                start_angle = angle_from_center(center, start)
                end_angle = angle_from_center(center, end)

                # 왼쪽/오른쪽 호 처리
                if ip.curve_direction == CurveDirection.RIGHT:
                    start_angle, end_angle = end_angle, start_angle

                self.msp.add_arc(
                    center=(center.x, center.y),
                    radius=r,
                    start_angle=start_angle,
                    end_angle=end_angle,
                    dxfattribs={'layer': 'FL'}
                )