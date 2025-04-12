from dataclasses import dataclass
from enum import Enum
from tkinter import filedialog
from typing import List, Optional

# 파일 읽기 함수
def read_file():
    global lines
    file_path = filedialog.askopenfilename()  # Open file dialog
    return file_path

@dataclass
class TextureCoordinate:
    vertex_index: int
    x: float
    y: float

class MeshBuilderCommand(Enum):
    CREATE = "CreateMeshBuilder"
    ADD_VERTEX = "AddVertex"
    ADD_FACE = "AddFace"
    ADD_FACE2 = "AddFace2"
    CUBE = "Cube"
    CYLINDER = "Cylinder"
    GENERATE_NORMALS = "GenerateNormals"
    SET_COLOR = "SetColor"  # 추가
    SET_COLOR_ALL = "SetColorAll"  # 추가

@dataclass
class Vertex:
    x: float
    y: float
    z: float
    nx: float = 0.0
    ny: float = 0.0
    nz: float = 0.0

@dataclass
class Face:
    vertex_indices: List[int]
    double_sided: bool = False
    color: Optional[tuple] = None  # 색상 정보 추가

@dataclass
class MeshBuilder:
    vertices: List[Vertex]
    faces: List[Face]
    daytime_texture: str = None
    nighttime_texture: str = None
    texture_coordinates: List[TextureCoordinate] = None
    color: Optional[tuple] = None  # 색상 정보 추가


def export_to_obj(meshes: List[MeshBuilder], filepath: str, mtl_filepath: str):
    with open(filepath, "w", encoding="utf-8") as f, open(mtl_filepath, "w", encoding="utf-8") as mtl_file:
        f.write("# Exported from BVE Object Viewer\n")
        f.write(f"mtllib {mtl_filepath}\n")

        vertex_offset = 1
        material_offset = 0

        for i, mesh in enumerate(meshes):
            f.write(f"\no Mesh_{i}\n")

            if mesh.color:
                mtl_name = f"material_{i + material_offset}"
                f.write(f"usemtl {mtl_name}\n")
                export_to_mtl(mtl_file, mtl_name, mesh.color, mesh.daytime_texture, mesh.nighttime_texture)

            for v in mesh.vertices:
                f.write(f"v {v.x} {v.y} {v.z}\n")

            if mesh.texture_coordinates:
                for tc in mesh.texture_coordinates:
                    f.write(f"vt {tc.x} {tc.y}\n")

            for face in mesh.faces:
                indices = [str(idx + vertex_offset) for idx in face.vertex_indices]
                f.write("f " + " ".join(indices) + "\n")

            vertex_offset += len(mesh.vertices)



def export_to_mtl(mtl_file, mtl_name: str, color: tuple,
                  daytime_texture: Optional[str] = None,
                  nighttime_texture: Optional[str] = None):
    r, g, b, a = color
    mtl_file.write(f"\n\n# Material: {mtl_name}\n")
    mtl_file.write(f"newmtl {mtl_name}\n")
    mtl_file.write(f"Kd {r / 255} {g / 255} {b / 255}\n")
    mtl_file.write(f"Ka {r / 255} {g / 255} {b / 255}\n")

    if daytime_texture:
        mtl_file.write(f"map_Kd {daytime_texture}\n")
    if nighttime_texture:
        mtl_file.write(f"#bve_nightmap {nighttime_texture}\n")  # OpenBVE 전용 주석 방식



def parse_object_file(file_path: str) -> List[MeshBuilder]:
    parser = ObjectParser()
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            # 주석과 빈 줄 무시
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                continue
            try:
                parser.parse_line(stripped)
            except Exception as e:
                print(f"[Line {line_num}] Error parsing line: {line.strip()}")
                print(f"  → {e}")
    return parser.meshes


class ObjectParser:
    def __init__(self):
        self.meshes: List[MeshBuilder] = []
        self.current_mesh: MeshBuilder = None
        self.previous_color: Optional[tuple] = None  # 이전 색상 추가

    def parse_line(self, line: str):
        tokens = [t.strip() for t in line.strip().split(",") if t.strip() != ""]
        if not tokens:
            return

        command = tokens[0]

        if command == "CreateMeshBuilder":
            self.current_mesh = MeshBuilder(vertices=[], faces=[], texture_coordinates=[])
            self.meshes.append(self.current_mesh)

        elif command == "AddVertex":
            try:
                floats = list(map(float, tokens[1:]))
                if len(floats) == 3:
                    self.current_mesh.vertices.append(Vertex(*floats))
                elif len(floats) == 6:
                    self.current_mesh.vertices.append(Vertex(*floats[:3], *floats[3:]))
                else:
                    raise ValueError("Invalid number of parameters for AddVertex")
            except ValueError as e:
                raise ValueError(f"Invalid float in AddVertex: {e}")

        elif command == "AddFace":
            indices = list(map(int, tokens[1:]))
            self.current_mesh.faces.append(Face(indices, double_sided=False))

        elif command == "AddFace2":
            indices = list(map(int, tokens[1:]))
            self.current_mesh.faces.append(Face(indices, double_sided=True))

        elif command == "LoadTexture":
            # LoadTexture 명령어 처리: 텍스처 파일 지정
            daytime_texture = tokens[1].strip()
            nighttime_texture = tokens[2].strip() if len(tokens) > 2 else None
            self.current_mesh.daytime_texture = daytime_texture
            self.current_mesh.nighttime_texture = nighttime_texture

        elif command == "SetTextureCoordinates":
            try:
                vertex_index = int(tokens[1])
                x = float(tokens[2])
                y = float(tokens[3])
                self.current_mesh.texture_coordinates.append(TextureCoordinate(vertex_index, x, y))
            except ValueError as e:
                raise ValueError(f"Invalid parameters in SetTextureCoordinates: {e}")

        elif command == "SetColor":
            try:
                red = int(tokens[1])
                green = int(tokens[2])
                blue = int(tokens[3])
                alpha = int(tokens[4])
                # 색상 설정
                self.current_mesh.color = (red, green, blue, alpha)
                # 이미 만들어진 면에 색상 적용
                for face in self.current_mesh.faces:
                    face.color = (red, green, blue, alpha)
            except ValueError as e:
                raise ValueError(f"Invalid parameters in SetColor: {e}")

        elif command == "SetColorAll":
            try:
                red = int(tokens[1])
                green = int(tokens[2])
                blue = int(tokens[3])
                alpha = int(tokens[4])
                # 색상 설정
                for mesh in self.meshes:
                    mesh.color = (red, green, blue, alpha)
                    for face in mesh.faces:
                        face.color = (red, green, blue, alpha)
            except ValueError as e:
                raise ValueError(f"Invalid parameters in SetColorAll: {e}")

        elif command == "Cube":
            pass  # TODO: Add cube handling logic

        elif command == "Cylinder":
            pass  # TODO: Add cylinder handling logic

        elif command == "GenerateNormals":
            pass


if __name__ == "__main__":
    filepath = read_file()
    meshes = parse_object_file(filepath)
    print(f"총 메시 개수: {len(meshes)}")
    for i, mesh in enumerate(meshes):
        print(f"Mesh {i}: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
        if mesh.color:
            print(f"  Mesh Color: {mesh.color}")

    # OBJ 파일 저장
    save_path = filedialog.asksaveasfilename(defaultextension=".obj", filetypes=[("OBJ files", "*.obj")])
    if save_path:
        # MTL 파일 경로 설정
        mtl_save_path = save_path.replace(".obj", ".mtl")

        # OBJ 파일 내보내기
        export_to_obj(meshes, save_path, mtl_save_path)
        print(f"OBJ 파일로 내보냈습니다: {save_path}")
