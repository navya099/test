from model.objmodel.interface.i3dobject import PreviewObject3D


class BracketObject3D(PreviewObject3D):
    def __init__(self, vertices, edges):
        self._vertices = vertices
        self._edges = edges

    def get_vertices(self):
        return self._vertices

    def get_edges(self):
        return self._edges
