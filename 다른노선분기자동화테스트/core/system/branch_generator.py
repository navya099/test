import numpy as np
import logging as log

class BranchGenerator:
    """자선 분기 곡선 생성기"""

    def __init__(self, start_coord, end_coord, num_points=20, method="linear"):
        """
        start_coord: (z, x, y) 시작 좌표
        end_coord: (z, x, y) 끝 좌표
        num_points: 곡선 분할 포인트 수
        method: 'linear', 'arc', 'clothoid' 중 선택
        """
        self.start = np.array(start_coord)
        self.end = np.array(end_coord)
        self.num_points = num_points
