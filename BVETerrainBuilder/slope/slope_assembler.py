from shapely.geometry import Polygon
from shapely.ops import unary_union

class SlopeAssembler:
    """사면끼리 교차 영역 제거"""
    def __init__(self, slope_lefts, slope_rights):
        self.slope_lefts = slope_lefts
        self.slope_rights = slope_rights

    def clip_slopes(self):
        cleaned_lefts = []
        cleaned_rights = []

        # 좌측 사면 클리핑
        left_polys = [Polygon(sl.points[:, :2]) for sl in self.slope_lefts]
        merged_left = unary_union(left_polys)
        for sl in self.slope_lefts:
            poly = Polygon(sl.points[:, :2])
            diff = poly.difference(merged_left)
            if not diff.is_empty and diff.geom_type == "Polygon":
                cleaned_lefts.append(sl)  # 필요하다면 diff 결과로 갱신

        # 우측 사면 클리핑
        right_polys = [Polygon(sr.points[:, :2]) for sr in self.slope_rights]
        merged_right = unary_union(right_polys)
        for sr in self.slope_rights:
            poly = Polygon(sr.points[:, :2])
            diff = poly.difference(merged_right)
            if not diff.is_empty and diff.geom_type == "Polygon":
                cleaned_rights.append(sr)

        return cleaned_lefts, cleaned_rights
