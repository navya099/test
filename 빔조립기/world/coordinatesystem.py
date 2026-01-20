# core/geometry/transform.py
from world.worldvec3 import WorldVec3


def sketchup_to_world(vertices):
    return [(x, z , y) for x, y, z in vertices]
