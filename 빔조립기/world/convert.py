from world.bve_transform import OpenBVETransform
from world.coordinatesystem import CoordinateSystem
from world.world_transform import WorldTransform


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