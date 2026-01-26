import numpy as np

from vector3 import Vector3


class ObjectModifier:
    def __init__(self, vertices=None):
        self.vertices = vertices
        self.pivot = None

    def rotate_x(self, angle_deg: float):
        theta = np.deg2rad(angle_deg)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        R = np.array([
            [1, 0, 0],
            [0, cos_t, -sin_t],
            [0, sin_t, cos_t],
        ])

        self.vertices = (
                                (self.vertices - self.pivot) @ R.T
                        ) + self.pivot

    def rotate_y(self, angle_deg: float):
        theta = np.deg2rad(angle_deg)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        R = np.array([
            [cos_t, 0, sin_t],
            [0, 1, 0],
            [-sin_t, 0, cos_t],
        ])

        self.vertices = (
                                (self.vertices - self.pivot) @ R.T
                        ) + self.pivot

    def rotate_z(self, angle_deg: float):
        theta = np.deg2rad(angle_deg)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        R = np.array([
            [cos_t, -sin_t, 0],
            [sin_t, cos_t, 0],
            [0, 0, 1],
        ])

        # 🔥 pivot 기준 회전
        self.vertices = (
            (self.vertices - self.pivot) @ R.T
        ) + self.pivot

    def translate_world(self, dx, dy, dz=0):
        """전역 좌표이동"""
        offset = np.array([dx, dy, dz])
        self.vertices = self.vertices + offset

    def translate_local(self, dx, dy, dz=0):
        """로컬 좌표이동"""
        offset = np.array([dx, dy, dz])
        self.vertices = (self.vertices - self.pivot) + offset + self.pivot

    def set_vertices(self, vertices):
        self.vertices = vertices

    def set_pivot(self, pivot: Vector3):
        if pivot is None:
            self.pivot = np.zeros(3)
            return

        if hasattr(pivot, "to_array"):
            self.pivot = pivot.to_array()
        else:
            raise TypeError(f"Invalid pivot type: {type(pivot)}")

