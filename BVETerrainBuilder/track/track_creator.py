import numpy as np


class TrackCreator:
    """OBJ 3D 트랙 생성 클래스"""

    def __init__(self, coords, track_width):
        self.coords = coords  # [(x,y,z)]
        self.track_width = track_width

    def create_track(self):
        """노선 중심 좌표에서 좌우 offset으로 트랙 메쉬 생성"""
        left_side = []
        right_side = []
        for i in range(len(self.coords) - 1):
            x1, y1, z1 = self.coords[i]
            x2, y2, z2 = self.coords[i + 1]
            dx, dy = x2 - x1, y2 - y1
            length = np.sqrt(dx ** 2 + dy ** 2)
            nx, ny = -dy / length, dx / length  # 수직 벡터
            left_side.append((x1 + nx * self.track_width / 2, y1 + ny * self.track_width / 2, z1))
            right_side.append((x1 - nx * self.track_width / 2, y1 - ny * self.track_width / 2, z1))

        # 좌우를 연결해 트랙 메쉬 생성
        vertices = np.array(left_side + right_side)
        faces = self.create_track_faces(left_side, right_side)
        return vertices, faces , left_side, right_side  # ✅ 둘 다 반환

    def create_track_faces(self, left_side, right_side):
        faces = []
        for i in range(len(left_side) - 1):
            # 좌측/우측 점 인덱스
            li, li_next = i, i + 1
            ri, ri_next = i + len(left_side), i + 1 + len(left_side)

            # 삼각형 두 개 생성
            faces.append([li, ri, li_next])
            faces.append([ri, ri_next, li_next])
        return faces