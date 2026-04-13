from data.segment.straight_segment import StraightSegment

class SegmentManager:
    def __init__(self):
        self.segment_list = []

    def build_segments(self, coord_list, groups):
        """BP→EP까지 순서대로 세그먼트 빌드"""
        segments = []

        for idx in range(len(coord_list) - 1):
            current_group = groups[idx]
            next_group = groups[idx + 1]

            # 현재 좌표의 끝점 결정
            if current_group:
                current_end = current_group.segments[-1].end_coord
                segments.extend(current_group.segments)
            else:
                current_end = coord_list[idx]

            # 다음 좌표의 시작점 결정
            if next_group:
                next_start = next_group.segments[0].start_coord
            else:
                next_start = coord_list[idx + 1]

            # 직선 연결
            self._append_unique(
                segments,
                StraightSegment.from_coord(start_point=current_end, end_point=next_start)
            )

        self.segment_list = segments
        self.update_prev_next_entity_id()
        self.update_stations()

    def _append_unique(self, segments, seg):
        """중복 방지 직선 추가"""
        for s in segments:
            if (s.start_coord == seg.start_coord and s.end_coord == seg.end_coord) or \
                    (s.start_coord == seg.end_coord and s.end_coord == seg.start_coord):
                return
        segments.append(seg)

    def update_prev_next_entity_id(self):
        """전체 세그먼트 인덱스 연결"""
        n = len(self.segment_list)

        # 1️⃣ current_index 먼저 부여
        for i, seg in enumerate(self.segment_list):
            seg.current_index = i

        # 2️⃣ prev, next는 이미 current_index가 세팅된 후 연결
        for i, seg in enumerate(self.segment_list):
            seg.prev_index = i - 1 if i > 0 else None
            seg.next_index = i + 1 if i < n - 1 else None

    def update_stations(self):
        """start_sta, end_sta 자동 계산"""
        current_sta = 0.0
        for seg in self.segment_list:
            seg.start_sta = current_sta
            seg.end_sta = current_sta + seg.length
            current_sta = seg.end_sta