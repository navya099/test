import numpy as np

from xref_module.objmodel.csvobject import CSVObject
from xref_module.vector3.vector3 import Vector3


class ObjectModifier:
    def __init__(self, csvobject: CSVObject):
        self.csvobject = csvobject
        self._np_pivot: np.ndarray | None = None

        # Mesh별 NumPy 캐시
        self._np_mesh_vertices: list[np.ndarray] = [
            self._to_np(mesh.vertices)
            for mesh in csvobject.meshes
        ]

    # ---------- Pivot ----------

    def set_pivot(self, pivot: Vector3):
        self._np_pivot = np.array(
            [pivot.x, pivot.y, pivot.z],
            dtype=float
        )

    # ---------- 회전 ----------

    def rotate_x(self, angle_deg: float):
        self._apply_rotation(self._rot_x(angle_deg))

    def rotate_y(self, angle_deg: float):
        self._apply_rotation(self._rot_y(angle_deg))

    def rotate_z(self, angle_deg: float):
        self._apply_rotation(self._rot_z(angle_deg))

    def _apply_rotation(self, R: np.ndarray):
        if self._np_pivot is None:
            raise ValueError("pivot is not set")

        self._np_mesh_vertices = [
            ((v - self._np_pivot) @ R.T) + self._np_pivot
            for v in self._np_mesh_vertices
        ]

    # ---------- 이동 ----------

    def translate_world(self, dx, dy, dz=0):
        offset = np.array([dx, dy, dz], dtype=float)
        self._np_mesh_vertices = [
            v + offset for v in self._np_mesh_vertices
        ]

    def translate_local(self, dx, dy, dz=0):
        if self._np_pivot is None:
            raise ValueError("pivot is not set")

        offset = np.array([dx, dy, dz], dtype=float)
        self._np_mesh_vertices = [
            (v - self._np_pivot) + offset + self._np_pivot
            for v in self._np_mesh_vertices
        ]

    # ---------- 적용 ----------

    def apply(self):
        """NumPy 결과를 CSVObject에 반영"""
        for mesh, np_vertices in zip(
            self.csvobject.meshes,
            self._np_mesh_vertices
        ):
            mesh.vertices = [
                Vector3(x, y, z)
                for x, y, z in np_vertices
            ]

    # ---------- 행렬 ----------

    def _rot_x(self, angle_deg):
        t = np.deg2rad(angle_deg)
        c, s = np.cos(t), np.sin(t)
        return np.array([
            [1, 0, 0],
            [0, c, -s],
            [0, s, c],
        ])

    def _rot_y(self, angle_deg):
        t = np.deg2rad(angle_deg)
        c, s = np.cos(t), np.sin(t)
        return np.array([
            [c, 0, s],
            [0, 1, 0],
            [-s, 0, c],
        ])

    def _rot_z(self, angle_deg):
        t = np.deg2rad(angle_deg)
        c, s = np.cos(t), np.sin(t)
        return np.array([
            [c, -s, 0],
            [s, c, 0],
            [0, 0, 1],
        ])

    def _to_np(self, vertices: list[Vector3]) -> np.ndarray:
        return np.array(
            [[v.x, v.y, v.z] for v in vertices],
            dtype=float
        )