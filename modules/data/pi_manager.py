from data.alignment.exception.alignment_error import NotEnoughPIPointError
from data.segment.straight_segment import StraightSegment
from point2d import Point2d


class PIManager:
    def __init__(self):
        self.coord_list = []
        self.radius_list = []

    def _insert_pi_in_segment(self, coord):
        """
        주어진 좌표 근처의 세그먼트에 PI를 삽입.
        :param coord: (x, y)
        :return: (삽입된 PI 인덱스)
        """


        # 2️⃣ 삽입 위치(해당 세그먼트의 인덱스) 찾기
        seg_index = nearest_seg.current_index

        #세그먼트 분활
        new_seg = nearest_seg.split_to_segment(coord)

        #세그먼트 리스트에 추가
        self.segment_list.insert(seg_index + 1, new_seg)
        #인덱스 갱신
        self._update_prev_next_entity_id()

        #pi인덱스 찾기
        prev_pi_index, next_pi_index = self._find_pi_interval(coord)
        self.coord_list.insert(next_pi_index, coord)

        #그룹 재조정
        group_index = 0
        for group in self.groups:
            for seg in  group.segments:
                if seg.current_index == nearest_seg.prev_index:
                    group_index = group.group_id - 1
                    break

        # 각각 그룹 갱신
        prev_group = self.groups[group_index]
        next_group = self.groups[group_index + 1]

        prev_group.update_by_pi(ep_coordinate=coord)
        next_group.update_by_pi(bp_coordinate=coord)

        #직선 세그먼트 갱신
        self._adjust_adjacent_straights(prev_group)
        self._adjust_adjacent_straights(next_group)

        #인덱스 및 그룹 및 station 갱신
        self._update_prev_next_entity_id()
        self._update_group_index()
        self._update_stations()

    def find_pi_interval(self, coord: Point2d) -> tuple[int, int]:
        """
        주어진 좌표(coord)가 어느 두 PI 사이에 속하는지 반환.
        (예: (1,2) → coord_list[1]과 coord_list[2] 사이)
        """
        if len(self.coord_list) < 2:
            raise NotEnoughPIPointError()

        min_dist = float('inf')
        nearest_index = None

        for i in range(len(self.coord_list) - 1):
            p1, p2 = self.coord_list[i], self.coord_list[i + 1]
            seg = StraightSegment(start_coord=p1, end_coord=p2)
            dist = seg.distance_to_point(coord)
            if dist < min_dist:
                min_dist = dist
                nearest_index = i

        return nearest_index, nearest_index + 1