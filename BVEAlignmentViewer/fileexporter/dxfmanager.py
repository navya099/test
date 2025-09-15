import ezdxf
from math_utils import angle_from_center, calculate_coordinates, degrees_to_dms
from model.model import IPdata, CurveType, CurveDirection, CurveSegment, SpiralSegment, BVERouteData
from utils import try_parse_int, format_distance
import math

from vector2 import Vector2
from vector3 import to2d


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
        '''
        # R문자
        self._draw_mtexts(ipdata, 'R문자',
                         lambda ip, i, n: None if i == 0 or i == n - 1 else f'\nR={ip.radius:.2f}' if isinstance(
                             ip.radius, float) else f'\nR1={ip.radius[0]:.2f}\nR2={ip.radius[1]:.2f}')
        '''
        #ip제원표
        self._draw_ip_table(ipdata)

        #곡선제원문자및 인출선
        self._draw_curve_text_and_line(ipdata, bvedata)

        #chain선 및 chian불록
        self._draw_chain(bvedata)
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
                            for k, coord in enumerate(bvedata.coords):
                                sta = bvedata.firstblock + k * bvedata.block_interval
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

    def _define_chain_blocks(self):
        # 25m tick 블록 정의
        blk = self.doc.blocks.new(name="CHAIN_TICK25")
        blk.add_line((-1.5, 0), (1.5, 0), dxfattribs={'color': 1, 'layer': 'byblock'})

        # 200m 작은 원 블록 정의
        blk = self.doc.blocks.new(name="CHAIN_CIRCLE200")
        blk.add_circle(center=(0, 0), radius=1.5, dxfattribs={'color': 2})

        # 1000m 큰 원 블록 정의
        blk = self.doc.blocks.new(name="CHAIN_CIRCLE1000")
        blk.add_circle(center=(0, 0), radius=2, dxfattribs={'color': 3})
    def _define_iptable_blocks(self):
        blk = self.doc.blocks.new(name="IPTABLE")
        layer = 'IPTABLE'
        color = 1
        height = 3
        #테두리
        blk.add_line((0, 0), (51, 0), dxfattribs={'color': color, 'layer': layer}) #하단 테두리
        blk.add_line((51, 0), (51, 51), dxfattribs={'color': color, 'layer': layer})#우측 테두리
        blk.add_line((51, 51), (0, 51), dxfattribs={'color': color, 'layer': layer})#상단 테두리
        blk.add_line((0, 51), (0, 0), dxfattribs={'color': color, 'layer': layer})#좌측테두리
        #태이블 내부 가로선
        blk.add_line((0, 7), (51, 7), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 14), (51, 14), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 21), (51, 21), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 28), (51, 28), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 35), (51, 35), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 42), (51, 42), dxfattribs={'color': color, 'layer': layer})
        #테이블 내부 세로선
        blk.add_line((12, 42), (12, 0), dxfattribs={'color': color, 'layer': layer})
        #테이블 내부 문자
        blk.add_text('IA',
                          dxfattribs={
                              'insert': (3, 37),
                              'height': height,
                              'color': color,
                              'layer': layer,
                          })
        blk.add_text('R',
                     dxfattribs={
                         'insert': (4.5, 30),
                         'height': height,
                         'color': color,
                         'layer': layer,
                     })
        blk.add_text('TL',
                     dxfattribs={
                         'insert': (3, 23),
                         'height': height,
                         'color': color,
                         'layer': layer,
                     })
        blk.add_text('CL',
                     dxfattribs={
                         'insert': (3, 16),
                         'height': height,
                         'color': color,
                         'layer': layer,
                     })
        blk.add_text('X',
                     dxfattribs={
                         'insert': (4.5, 9),
                         'height': height,
                         'color': color,
                         'layer': layer,
                     })
        blk.add_text('Y',
                     dxfattribs={
                         'insert': (4.5, 2),
                         'height': height,
                         'color': color,
                         'layer': layer,
                     })
        # IPNO 속성
        blk.add_attdef(tag="IPNO", insert=(18, 44), height=3, text="0", dxfattribs={'layer': 'attr'})
        # IA 속성
        blk.add_attdef(tag="IA", insert=(14.25, 38.5), height=3, text="0", dxfattribs={'layer': 'attr'})
        # R 속성
        blk.add_attdef(tag="R", insert=(14.25, 31.5), height=3, text="0", dxfattribs={'layer': 'attr'})
        # TL 속성
        blk.add_attdef(tag="TL", insert=(14.25, 24.5), height=3, text="0", dxfattribs={'layer': 'attr'})
        # CL 속성
        blk.add_attdef(tag="CL", insert=(14.25, 17.5), height=3, text="0", dxfattribs={'layer': 'attr'})
        # X 속성
        blk.add_attdef(tag="X", insert=(14.25, 10.55), height=3, text="0", dxfattribs={'layer': 'attr'})
        # Y 속성
        blk.add_attdef(tag="Y", insert=(14.25, 3.5), height=3, text="0", dxfattribs={'layer': 'attr'})

    def _define_curvespec_blocks(self):
        blk = self.doc.blocks.new(name="곡선인출블럭")
        layer = '곡선제원'
        color = 1
        height = 3
        #인출선
        blk.add_line((0, 0), (70, 0), dxfattribs={'color': color, 'layer': layer})
        #인출텍스트
        #곡선제원문자속성
        blk.add_attdef(tag="type", insert=(30, 3.5), height=height, text="0", dxfattribs={'layer': 'attr'})
        # 곡선위치속성
        blk.add_attdef(tag="sta", insert=(40, 3.5), height=height, text="0", dxfattribs={'layer': 'attr'})

    def _draw_chain(self, bvedata: BVERouteData):
            #chain불록 생성
            self._define_chain_blocks()
            #선형에 배치
            for i, coord in enumerate(bvedata.coords):
                sta = bvedata.firstblock + i * bvedata.block_interval
                angle = to2d(bvedata.directions[i]).todegree() #선형진행각도
                normalize_angle = angle - 90 #선형에 수직인 각도
                offset_coord = calculate_coordinates(coord.x, coord.y, normalize_angle, 2)
                kmtext = f"{sta // 1000}km"  # 몫만 사용
                mtext = f"{int(sta % 1000):03d}"  # 3자리로 맞춤
                #chian 선
                self.msp.add_blockref("CHAIN_TICK25", insert=(coord.x, coord.y), dxfattribs={"rotation": normalize_angle})
                # 200m 작은 원
                if sta % 200 == 0:
                    self.msp.add_blockref("CHAIN_CIRCLE200", insert=(coord.x, coord.y), dxfattribs={"rotation": normalize_angle})
                if sta % 200 == 0 and sta % 1000 != 0:
                    self.msp.add_text(mtext,
                        dxfattribs={
                            'insert': (offset_coord[0], offset_coord[1]),
                            'height': 3,
                            'color': 1,
                            'layer': '200문자',
                            'rotation': angle,
                        })
                #1km원
                if sta % 1000 == 0:
                    self.msp.add_blockref("CHAIN_CIRCLE1000", insert=(coord.x, coord.y), dxfattribs={"rotation": angle})
                    self.msp.add_text(kmtext,
                        dxfattribs={
                            'insert': (offset_coord[0], offset_coord[1]),
                            'height': 3,
                            'color': 1,
                            'layer': 'km문자',
                            'rotation': angle,
                        })
    def _draw_ip_table(self, iplist: list[IPdata]):
        self._define_iptable_blocks()
        for i, ip in enumerate(iplist):
            if i != 0 and i != len(iplist) - 1:
                iatext = degrees_to_dms(math.degrees(ip.ia))
                cl_value = max(
                    getattr(seg, "total_length", getattr(seg, "length", 0))
                    for seg in ip.segment
                )
                radius = f'{ip.radius:.3f}'
                tl = max(seg.tl for seg in ip.segment)
                tl = f'{tl:.3f}'
                cl = f'{cl_value:.3f}'
                x = f'{ip.coord.y:.4f}'
                y = f'{ip.coord.x:.4f}'
                block_ref = self.msp.add_blockref(
                    name="IPTABLE",
                    insert=(ip.coord.x, ip.coord.y),
                    dxfattribs={
                        "layer": "IPTABLE"
                    }
                )
                block_ref.add_auto_attribs({
                        "IPNO": f'IP. {ip.ipno}' if isinstance(ip.ipno, int) else ip.ipno,
                        "IA": iatext,
                        "R": radius,
                        "TL": tl,
                        "CL": cl,
                        "X": x,
                        "Y": y
                })

    def _draw_curve_text_and_line(self, iplist: list[IPdata], bvedata: BVERouteData):
        self._define_curvespec_blocks()
        for i, ip in enumerate(iplist):
            if i == 0:
                self._add_curve_block(ip.coord, 'BP', bvedata.firstblock, CurveDirection.LEFT, to2d(bvedata.directions[0]).toradian())
            elif i == len(iplist) - 1:
                self._add_curve_block(ip.coord, 'EP', bvedata.lastblock, CurveDirection.LEFT, to2d(bvedata.directions[-1]).toradian())
            else:
                if ip.curvetype == CurveType.Spiral:
                    for seg in ip.segment:
                        if isinstance(seg, SpiralSegment):
                            if seg.isstarted:
                                self._add_curve_block(seg.start_coord, 'SP', seg.start_sta, ip.curve_direction, seg.start_azimuth)
                                self._add_curve_block(seg.end_coord, 'PC', seg.end_sta, ip.curve_direction, seg.end_azimuth)
                            else:
                                self._add_curve_block(seg.start_coord, 'CP', seg.start_sta, ip.curve_direction, seg.start_azimuth)
                                self._add_curve_block(seg.end_coord, 'PS', seg.end_sta, ip.curve_direction, seg.end_azimuth)
                        else:
                            pass
                elif ip.curvetype == CurveType.Simple:
                    seg = ip.segment[0]
                    self._add_curve_block(seg.start_coord, 'BC', seg.start_sta, ip.curve_direction, seg.start_azimuth)
                    self._add_curve_block(seg.end_coord, 'EC', seg.end_sta, ip.curve_direction, seg.end_azimuth)
                else:  # Complex
                    for j, seg in enumerate(ip.segment):

                        if j == 0:
                            self._add_curve_block(seg.start_coord, 'BC', seg.start_sta, ip.curve_direction,
                                                  seg.start_azimuth)
                            self._add_curve_block(seg.end_coord, 'PCC', seg.end_sta, ip.curve_direction, seg.end_azimuth)
                        else:
                            self._add_curve_block(seg.end_coord, 'EC', seg.end_sta, ip.curve_direction,
                                                  seg.end_azimuth)
    def _add_curve_block(self, coord: Vector2, curve_type: str, sta: float, direction: CurveDirection, angle: float):
        xscale = 1 if direction == CurveDirection.RIGHT else -1
        yscale = 1 if direction == CurveDirection.RIGHT else -1
        angle = math.degrees(angle)
        block_ref = self.msp.add_blockref(
            name="곡선인출블럭",
            insert=(coord.x, coord.y),
            dxfattribs={
                "layer": "곡선인출블럭",
                "xscale": xscale,
                "yscale": yscale,
                "rotation":angle - 90
            }
        )
        block_ref.add_auto_attribs({
            "type": f'{curve_type}= ',
            "sta": format_distance(sta)
        })
