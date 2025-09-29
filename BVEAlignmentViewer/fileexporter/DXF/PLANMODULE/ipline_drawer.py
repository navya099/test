from model.ipdata import IPdata


class IPLINEDrawer:
    def __init__(self, msp):
        self.msp = msp

    def draw_ipline(self, ipdata: list[IPdata]):
        points = [(ip.coord.x, ip.coord.y) for ip in ipdata]
        lwpolyline = self.msp.add_lwpolyline(points, dxfattribs={'layer': 'IP라인'})