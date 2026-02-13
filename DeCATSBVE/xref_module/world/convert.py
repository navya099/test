from xref_module.world.bve_transform import OpenBVETransform
from xref_module.world.coordinatesystem import CoordinateSystem
from xref_module.world.world_transform import WorldTransform


class CoordinateConverter:
    def __init__(self):

        self._map = {
            CoordinateSystem.OPENBVE: OpenBVETransform(),
            CoordinateSystem.WORLD: WorldTransform(),
        }

    def convert(self, csvobj, target: CoordinateSystem):
        if csvobj.coordsystem == target:
            return

        src_tf = self._map[csvobj.coordsystem]
        dst_tf = self._map[target]

        for mesh in csvobj.meshes:
            mesh.vertices = [
                dst_tf.from_world(
                    src_tf.to_world(v)
                )
                for v in mesh.vertices
            ]

        csvobj.coordsystem = target

    # -----------------------------
    # 단일 점 변환
    # -----------------------------
    def convert_point(self, point, target: CoordinateSystem):
        """
        point: Vector3 (현재 좌표계)
        target: 변환할 목표 좌표계
        return: Vector3 (target 좌표계)
        """
        # 기본 좌표계는 OPENBVE 기준이라면, point.coordsystem 필요 없으면 csvobj.coordsystem 사용 가능
        # 여기서는 point가 현재 transform 좌표계라고 가정
        # 임시 src_tf 지정
        # 필요 시 인자로 src 좌표계 받도록 확장 가능
        src_tf = self._map[CoordinateSystem.OPENBVE]  # 현재 pivot이 SketchUp/OpenBVE 기준이라면
        dst_tf = self._map[target]

        world_v = src_tf.to_world(point)  # 현재 좌표계 → WORLD

        return world_v