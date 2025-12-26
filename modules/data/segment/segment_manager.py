from data.alignment.geometry.segmentgeometry import SegmentGeometry
from data.alignment.geometry.straight.straightgeometry import StraightGeometry
from data.segment.curve_segment import CurveSegment
from data.segment.exception.segment_exception import SegmentNotFoundError
from data.segment.segment_group.segment_group import SegmentGroup

from data.segment.straight_segment import StraightSegment
from point2d import Point2d


class SegmentManager:
    def __init__(self):
        self.segment_list = []

    def find_nearest_segment(self, coord: Point2d):
        """세그먼트 리스트에서 점에 가장 가까운 세그먼트 탐색"""
        nearest_seg = min(
            self.segment_list,
            key=lambda seg: seg.distance_to_point(coord)
        )
        if nearest_seg is None:
            raise SegmentNotFoundError()
        if isinstance(nearest_seg, CurveSegment):
            raise ValueError('곡선 세그먼트에 pi를 추가할 수 없습니다.')
        return nearest_seg

    def adjust_adjacent_straights(self, group: SegmentGroup):
        """
        target_group 앞/뒤 직선 세그먼트의 start_coord, end_coord 조정
        """
        # 이전 직선
        prev_idx = group.segments[0].prev_index
        if prev_idx is not None:
            prev_seg = self.segment_list[prev_idx]
            if isinstance(prev_seg, StraightSegment):
                geom = StraightGeometry(start_coord=prev_seg.start_coord,end_coord=group.segments[0].start_coord)
                prev_seg._geom = geom
        # 다음 직선
        next_idx = group.segments[-1].next_index
        if next_idx is not None:
            next_seg = self.segment_list[next_idx]
            if isinstance(next_seg, StraightSegment):
                geom = StraightGeometry(start_coord=group.segments[-1].end_coord, end_coord=next_seg.end_coord)
                next_seg._geom = geom

    def adjust_adjacent_straights_without_group(self, old_coord: Point2d, new_coord: Point2d, tol: float = 1e-6):
        """
        곡선 그룹이 없는 상태에서 PI 이동 시 직선 연결점 조정
        - old_coord: 이동 전 PI 좌표
        - new_coord: 이동 후 PI 좌표
        """
        for seg in self.segment_list:
            if not isinstance(seg, StraightSegment):
                continue

            # 이전 PI 기준으로 직선 후보 찾기
            if seg.end_coord.distance_to(old_coord) < tol:
                seg.end_coord = new_coord

            if seg.start_coord.distance_to(old_coord) < tol:
                seg.start_coord = new_coord


    def remove_segments(self, target_group):
        """타깃 그룹과 그 내부 세그먼트 제거 후, 이전·다음 세그먼트 인덱스 반환"""
        prev_seg_index = target_group.segments[0].prev_index
        next_seg_index = target_group.segments[-1].next_index

        # 직선 세그먼트 탐색
        prev_seg = self.segment_list[prev_seg_index] if 0 <= prev_seg_index < len(self.segment_list) else None
        next_seg = self.segment_list[next_seg_index] if 0 <= next_seg_index < len(self.segment_list) else None

        # 그룹 세그먼트 제거
        for seg in list(target_group.segments):
            if seg in self.segment_list:
                self.segment_list.remove(seg)

        return prev_seg, next_seg

    def delete_segment_in_list(self, seg):
        self.segment_list.remove(seg)

    def find_straight_by_coord(self, coord):
        segs = []
        for seg in self.segment_list:
            if isinstance(seg, StraightSegment) and (seg.start_coord == coord or seg.end_coord == coord):
                segs.append(seg)
        return segs


