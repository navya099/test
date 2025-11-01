from point2d import Point2d


class SegmentManager:
    def __init__(self):
        self.segment_list = []

    def _process_segment_at_index(self, i):
        bp = self.coord_list[i]
        ep = self.coord_list[i + 1]

        # 곡선 처리
        if 0 < i < len(self.coord_list) - 1:
            group = self._create_curve_group(i)
            if group is None:
                print("해결할 수 있는 솔루션이 없습니다.")
                self.groups.clear()
                self.segment_list.clear()
                return

            self.groups.append(group)
            self._adjust_previous_straight(group)
            self.segment_list.extend(group.segments)
            self._append_next_straight(group, i)
        else:
            # 첫/마지막 직선
            straight = StraightSegment(start_coord=bp, end_coord=ep)
            self.segment_list.append(straight)

    def find_nearest_segment(self, coord: Point2d):
        """세그먼트 리스트에서 점에 가장 가까운 세그먼트 탐색"""
        nearest_seg = min(
            self.segment_list,
            key=lambda seg: seg.distance_to_point(coord)
        )
        return nearest_seg