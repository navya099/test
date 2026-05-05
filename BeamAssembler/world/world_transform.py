from world.base_transform import CoordinateTransform


class WorldTransform(CoordinateTransform):
    def to_world(self, v):
        return v

    def from_world(self, v):
        return v