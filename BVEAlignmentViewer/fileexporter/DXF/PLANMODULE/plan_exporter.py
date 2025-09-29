from Profile.profile import Profile
from fileexporter.DXF.PLANMODULE.chain_drawer import ChainDrawer
from fileexporter.DXF.PLANMODULE.curve_drawer import CurveDrawer
from fileexporter.DXF.PLANMODULE.fl_drawer import FLDrawer
from fileexporter.DXF.PLANMODULE.ipline_drawer import IPLINEDrawer
from fileexporter.DXF.PLANMODULE.iptable_drawer import IPTableDrawer
from fileexporter.DXF.PLANMODULE.station_drawer import StationDrawer
from fileexporter.DXF.PLANMODULE.texts_drawer import TextsDrawer
from model.bveroutedata import BVERouteData
from model.ipdata import IPdata
from utils import try_parse_int

class DXFPlanExporter:
    def __init__(self, doc, msp):
        self.doc = doc
        self.msp = msp

        # 책임 단위 모듈 생성
        self.ipline_drawer = IPLINEDrawer(msp)
        self.fl_drawer = FLDrawer(msp)
        self.texts_drawer = TextsDrawer(msp)
        self.curve_drawer = CurveDrawer(msp)
        self.chain_drawer = ChainDrawer(msp)
        self.iptable_drawer = IPTableDrawer(msp)
        self.station_drawer = StationDrawer(msp)

    def export_plandrawing(self, ipdata: list[IPdata], bvedata: BVERouteData ,profile: Profile):

        # IP라인 그리기
        self.ipline_drawer.draw_ipline(ipdata)

        #FL 그리기
        self.fl_drawer.draw_fl(ipdata ,bvedata)

        # IP문자
        self.texts_drawer.draw_texts(ipdata, 'IP문자',
                         lambda ip, i, n: 'BP' if i == 0 else 'EP' if i == n - 1 else f'IP{ip.ipno}' if try_parse_int(
                             ip.ipno) else str(ip.ipno))
        #ip제원표
        self.iptable_drawer.draw_ip_table(ipdata)

        #곡선제원문자및 인출선
        self.curve_drawer.draw_curve_text_and_line(ipdata, bvedata)

        #chain선 및 chian불록
        self.chain_drawer.draw_chain(bvedata)
        #정거장 위치
        self.station_drawer.draw_station_marker(bvedata)











