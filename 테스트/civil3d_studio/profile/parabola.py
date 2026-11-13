from profile.profile_entity import ProfileEntity


class ProfileParabola(ProfileEntity):
    """대칭/비대칭 포물선 종단곡선 순수 객체"""
    def __init__(self, start_sta: float, end_sta: float, pvi_sta: float,
                 bvc_el: float, evc_el: float, g1: float, g2: float,
                 l1: float, l2: float, e_offset: float):
        super().__init__(start_sta, end_sta)
        self.pvi_sta = float(pvi_sta)
        self.bvc_el = float(bvc_el)
        self.evc_el = float(evc_el)
        self.g1 = float(g1)
        self.g2 = float(g2)
        self.l1 = float(l1)
        self.l2 = float(l2)
        self.e_offset = float(e_offset)

    def elevation_and_grade_at(self, station: float):
        if station <= self.pvi_sta:
            x1 = max(0.0, station - self.start_sta)
            if self.l1 <= 1e-12:
                return self.bvc_el, self.g1
            el = self.bvc_el + self.g1 * x1 + self.e_offset * ((x1 / self.l1) ** 2)
            grade = self.g1 + (2.0 * self.e_offset / (self.l1 ** 2)) * x1
            return el, grade
        else:
            x2 = max(0.0, self.end_sta - station)
            if self.l2 <= 1e-12:
                return self.evc_el, self.g2
            el = self.evc_el - self.g2 * x2 + self.e_offset * ((x2 / self.l2) ** 2)
            grade = self.g2 - (2.0 * self.e_offset / (self.l2 ** 2)) * x2
            return el, grade