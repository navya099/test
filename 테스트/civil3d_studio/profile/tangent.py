from profile.profile_entity import ProfileEntity


class ProfileTangent(ProfileEntity):
    """직선 경사 구간 순수 객체"""
    def __init__(self, start_sta: float, end_sta: float, start_el: float, grade: float):
        super().__init__(start_sta, end_sta)
        self.start_el = float(start_el)
        self.grade = float(grade)

    def elevation_and_grade_at(self, station: float):
        ds = station - self.start_sta
        el = self.start_el + self.grade * ds
        return el, self.grade