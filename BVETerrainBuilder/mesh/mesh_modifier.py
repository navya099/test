import numpy as np


class MeshModifier:
    def __init__(self, mesh):
        self.mesh = mesh

    def translate(self, offset):
        """메쉬를 offset(x,y,z)만큼 평행이동"""
        self.mesh.points = self.mesh.points + np.array(offset)
        return self.mesh
