from alignment.arc import ArcSegment
from alignment.japancubic import JapaneseCubicSpiralSegment
from alignment.line import LineSegment
from alignment.aync import PIPoint
from profile.pvi import PVIPoint
from superelevation.superelevation import SuperelevationStation
import math

class RoadModel3D:
    """평면 + 종단 + 편경사 + 버스베이 확폭을 통합한 3D 도로 모델"""
    def __init__(self):

        pis = [
            PIPoint("BP",   200000.0, 500000.0),
            PIPoint("IP-1", 200380.0, 500220.0, R=320.0, L1=80.0, L2=70.0),
            PIPoint("IP-2", 200780.0, 500020.0, R=280.0, L1=70.0, L2=80.0),
            PIPoint("IP-3", 201180.0, 500280.0, R=350.0, L1=80.0, L2=80.0),
            PIPoint("EP",   201550.0, 500150.0),
        ]
        self.entities = []
        self._build_horizontal(pis)
        self.total_length = self.entities[-1].end_sta

        self.pvis = [
            PVIPoint("BVP",   0.0,               40.0),
            PVIPoint("PVI-1", 380.0,             51.5, L1=110.0, L2=110.0),
            PVIPoint("PVI-2", 820.0,             41.0, L1=100.0, L2=120.0),
            PVIPoint("PVI-3", 1220.0,            48.5, L1=90.0,  L2=90.0),
            PVIPoint("EVP",   self.total_length, 44.0),
        ]
        self.v_segs = []
        self._build_vertical()

        self.supers = [
            SuperelevationStation(0.0,    -0.02, -0.02),
            SuperelevationStation(210.0,  -0.02, -0.02),
            SuperelevationStation(290.0,   0.06, -0.06),
            SuperelevationStation(440.0,   0.06, -0.06),
            SuperelevationStation(510.0,  -0.02, -0.02),
            SuperelevationStation(620.0,  -0.02, -0.02),
            SuperelevationStation(690.0,  -0.06,  0.06),
            SuperelevationStation(860.0,  -0.06,  0.06),
            SuperelevationStation(940.0,  -0.02, -0.02),
            SuperelevationStation(1060.0, -0.02, -0.02),
            SuperelevationStation(1140.0,  0.05, -0.05),
            SuperelevationStation(1320.0,  0.05, -0.05),
            SuperelevationStation(1400.0, -0.02, -0.02),
        ]

    def _build_horizontal(self, pis):
        n = len(pis)
        bearings, lens = [], []
        for i in range(n - 1):
            de, dn = pis[i + 1].easting - pis[i].easting, pis[i + 1].northing - pis[i].northing

            bearings.append(math.atan2(dn, de))
            lens.append(math.hypot(de, dn))

        c_params = []
        for i in range(1, n - 1):
            pi = pis[i]
            R, L1, L2 = pi.R, pi.L1 or 0.0, pi.L2 or (pi.L1 or 0.0)
            d_th = (bearings[i] - bearings[i - 1] + math.pi) % (2.0 * math.pi) - math.pi
            IA, tdir = abs(d_th), (1 if d_th >= 0 else -1)

            def sh(rv, lv):
                if lv <= 0:
                    return 0.0, 0.0, 0.0
                t = JapaneseCubicSpiralSegment(0, 0, 0, 0, rv, lv, 1)
                return t.tau, t.Yc - rv * (1.0 - math.cos(t.tau)), t.Xc - rv * math.sin(t.tau)

            t1, dr1, xm1 = sh(R, L1)
            t2, dr2, xm2 = sh(R, L2)
            tl1 = xm1 + (R + dr1) * math.tan(IA * 0.5) + (dr2 - dr1) / math.sin(IA)
            tl2 = xm2 + (R + dr2) * math.tan(IA * 0.5) + (dr1 - dr2) / math.sin(IA)
            cl = R * (IA - t1 - t2)
            c_params.append((R, L1, L2, tdir, tl1, tl2, cl))

        ce, cn, c_sta = pis[0].easting, pis[0].northing, 0.0
        for i in range(n - 1):
            ptl2 = c_params[i - 1][5] if i > 0 else 0.0
            ntl1 = c_params[i][4] if i < n - 2 else 0.0
            slen = lens[i] - ptl2 - ntl1
            if slen > 1e-6:

                seg = LineSegment(ce, cn, bearings[i], c_sta, slen)
                self.entities.append(seg)
                ce, cn, _, c_sta = seg.end_pose
            if i < n - 2:
                R, L1, L2, tdir, _, _, cl = c_params[i]
                ca = bearings[i]
                if L1 > 1e-6:
                    s1 = JapaneseCubicSpiralSegment(ce, cn, ca, c_sta, R, L1, tdir, False)
                    self.entities.append(s1)
                    ce, cn, ca, c_sta = s1.end_pose
                if cl > 1e-6:
                    arc = ArcSegment(ce, cn, ca, c_sta, R, cl, tdir)
                    self.entities.append(arc)
                    ce, cn, ca, c_sta = arc.end_pose
                if L2 > 1e-6:
                    s2 = JapaneseCubicSpiralSegment(ce, cn, ca, c_sta, R, L2, tdir, True)
                    self.entities.append(s2)
                    ce, cn, _, c_sta = s2.end_pose

    def _build_vertical(self):
        n = len(self.pvis)
        grades = [(self.pvis[i + 1].elevation - self.pvis[i].elevation) /
                  (self.pvis[i + 1].station - self.pvis[i].station) for i in range(n - 1)]
        cs, ce = self.pvis[0].station, self.pvis[0].elevation
        for i in range(1, n - 1):
            p = self.pvis[i]
            g1, g2 = grades[i - 1], grades[i]
            bs, es = p.station - p.L1, p.station + p.L2
            be, ee = p.elevation - g1 * p.L1, p.elevation + g2 * p.L2
            tot = p.L1 + p.L2
            eo = ((g2 - g1) * p.L1 * p.L2) / (2.0 * tot) if tot > 0 else 0.0
            if bs > cs + 1e-6:
                self.v_segs.append(("T", cs, bs, ce, g1))
            if tot > 1e-6:
                self.v_segs.append(("P", bs, es, p.station, be, ee, g1, g2, p.L1, p.L2, eo))
            cs, ce = es, ee
        if self.pvis[-1].station > cs + 1e-6:
            self.v_segs.append(("T", cs, self.pvis[-1].station, ce, grades[-1]))

    def point_xy(self, sta: float, off: float = 0.0):
        s = max(0.0, min(self.total_length, sta))
        for ent in self.entities:
            if ent.start_sta - 1e-6 <= s <= ent.end_sta + 1e-6:
                return ent.point_location(s, off)
        return self.entities[-1].point_location(self.total_length, off)

    def elevation_grade(self, sta: float):
        s = max(0.0, min(self.total_length, sta))
        for seg in self.v_segs:
            if seg[1] - 1e-6 <= s <= seg[2] + 1e-6:
                if seg[0] == "T":
                    return seg[3] + seg[4] * (s - seg[1]), seg[4]
                _, bs, es, ps, be, ee, g1, g2, l1, l2, eo = seg
                if s <= ps:
                    x1 = max(0.0, s - bs)
                    return be + g1 * x1 + eo * ((x1 / l1) ** 2), g1 + (2.0 * eo / (l1 ** 2)) * x1
                x2 = max(0.0, es - s)
                return ee - g2 * x2 + eo * ((x2 / l2) ** 2), g2 - (2.0 * eo / (l2 ** 2)) * x2
        return self.pvis[-1].elevation, 0.0

    def get_slopes_and_widths(self, sta: float):
        # 편경사 선형 보간
        l_slp, r_slp = -0.02, -0.02
        for i in range(len(self.supers) - 1):
            s1, s2 = self.supers[i], self.supers[i + 1]
            if s1.station <= sta <= s2.station:
                t = (sta - s1.station) / max(1e-6, s2.station - s1.station)
                l_slp = s1.left_slope + t * (s2.left_slope - s1.left_slope)
                r_slp = s1.right_slope + t * (s2.right_slope - s1.right_slope)
                break
        # 우측 버스베이 확폭 구간 (STA 80 ~ 190m 구간에서 우측 폭 +3.5m -> +6.5m)
        r_width = 3.5
        if 80.0 <= sta <= 190.0:
            if sta < 105.0:
                t = (sta - 80.0) / 25.0
                r_width += 3.0 * (3 * t * t - 2 * (t ** 3))
            elif sta > 165.0:
                t = (190.0 - sta) / 25.0
                r_width += 3.0 * (3 * t * t - 2 * (t ** 3))
            else:
                r_width += 3.0
        return l_slp, r_slp, 3.5, r_width

    def cross_section_3d(self, sta: float):
        """지정 측점의 횡단 3D 정점 딕셔너리 반환"""
        cl_e, cl_n = self.point_xy(sta, 0.0)
        cl_z, grade = self.elevation_grade(sta)
        l_slp, r_slp, l_w, r_w = self.get_slopes_and_widths(sta)
        l_etw_z = cl_z + l_w * l_slp
        r_etw_z = cl_z + r_w * r_slp
        # 길어깨(1.5m, -4%) 및 사면(2.5m, 1:2)
        l_eps_off, r_eps_off = -(l_w + 1.5), (r_w + 1.5)
        l_eps_z, r_eps_z = l_etw_z - 1.5 * 0.04, r_etw_z - 1.5 * 0.04
        l_day_off, r_day_off = l_eps_off - 2.5, r_eps_off + 2.5
        l_day_z, r_day_z = l_eps_z - 2.5 * 0.5, r_eps_z - 2.5 * 0.5
        return {
            "CL":      (cl_e, cl_n, cl_z),
            "L_ETW":   (*self.point_xy(sta, -l_w), l_etw_z),
            "R_ETW":   (*self.point_xy(sta, +r_w), r_etw_z),
            "L_EPS":   (*self.point_xy(sta, l_eps_off), l_eps_z),
            "R_EPS":   (*self.point_xy(sta, r_eps_off), r_eps_z),
            "L_DAY":   (*self.point_xy(sta, l_day_off), l_day_z),
            "R_DAY":   (*self.point_xy(sta, r_day_off), r_day_z),
            "meta":    (cl_z, grade, l_slp, r_slp, l_w, r_w)
        }
