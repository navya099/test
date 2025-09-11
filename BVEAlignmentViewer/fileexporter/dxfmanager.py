import ezdxf

from model.model import IPdata, CurveType, CurveDirection

class DXFController:
    def __init__(self):
        self.msp = None
        self.doc = None

    def export_dxf(self, ipdata: list[IPdata], filepath: str):
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()

        # IP라인 그리기
        self._draw_ipline(ipdata)
        # FL 그리기
        self._draw_arc(ipdata)
        #저장
        self.doc.saveas(filepath)

    def _draw_ipline(self, ipdata: list[IPdata]):
        points = [(ip.coord.x, ip.coord.y) for ip in ipdata]
        lwpolyline = self.msp.add_lwpolyline(points)

    def _draw_arc(self, ipdata: list[IPdata]):
        """
        ipdata를 바탕으로 호 객체를 그리는 메소드
        Args:
            ipdata:

        Returns:
            msp.arc
        """
        for i, ip in enumerate(ipdata):
            if i ==0:
                #BP 생략
                continue
            elif i== len(ipdata)-1:
                #EP 생략
                continue
            else:
                #ip내부 호 객체 요소 추출
                if ip.curvetype == CurveType.Simple:
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
                else:
                    continue