from xref_module.objmodel.mesh.mesh import Mesh


class CSVObject:
    def __init__(
        self,
        meshes: list[Mesh],
        material=None,
        filename: str | None = None,
    ):
        self.meshes = meshes
        self.material = material
        self.filename = filename
        self.coordsystem = None