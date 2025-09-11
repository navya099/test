import ezdxf

from model.model import IPdata


class DXFController:
    def __init__(self):
        self.msp = None
        self.doc = None

    def export_dxf(self, ipdata: list[IPdata], filepath: str):
        self.doc = ezdxf.new()
        self.msp = self.doc.modelspace()

        # IP라인 그리기
        self._draw_ipline(ipdata)
        #저장
        self.doc.saveas(filepath)

    def _draw_ipline(self, ipdata: list[IPdata]):
        points = [(ip.coord.x, ip.coord.y) for ip in ipdata]
        lwpolyline = self.msp.add_lwpolyline(points)