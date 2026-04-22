import meshio
import numpy as np

from track.track_creator import TrackCreator


class TrackProcessor:
    """트랙 처리 클래스"""
    def __init__(self, coords):
        self.trm = TrackCreator(coords, track_width=6)

    def build_track(self):
        """트랙 생성"""
        vertices, faces , left_side, right_side = self.trm.create_track()
        return meshio.Mesh(points=vertices, cells=[("triangle", np.array(faces))]), [left_side, right_side]