from abc import ABC, abstractmethod


class BasePoleBuilder(ABC):
    """기본 추상 기둥 빌더"""
    def __init__(self, length, diameter):
        self.length = length #
        self.diameter = diameter
        self.text = []
        self.path = ''

    @abstractmethod
    def build(self):
        self.text = []
        raise NotImplementedError

    def _build_header(self):
        self.text.append('\n;by BeamAsemmbler Templete created\n')
        self.text.append('CreateMeshBuilder,\n')

    def save_text(self, filename):
        """csv저장"""
        self.path = filename
        with open(self.path, 'w', encoding='utf-8') as f:
            f.writelines(self.text)

    def v(self, x, y, z, nx, ny, nz):
        """버텍스 생성"""
        self.text.append(
            f'AddVertex, {x:.6f}, {y:.6f}, {z:.6f}, {nx}, {ny}, {nz},\n'
        )

    def addface(self, idx1, idx2, idx3, isface2=False):
        """페이스 생성"""
        face = 'AddFace' if not isface2 else 'AddFace2'
        self.text.append(
            f'{face}, {idx1}, {idx2}, {idx3},\n'
        )

    def load_texture(self, texturefile_name):
        self.text.append(
            f'LoadTexture, {texturefile_name},\n'
        )
    def set_color(self, r=0, g=0, b=0,a=0):
        self.text.append(
            f'SetColor, {r}, {g}, {b}, {a},\n'
        )
    def set_texture_coordinates(self, idx, u, v):
        self.text.append(
            f'SetTextureCoordinates, {idx}, {u}, {v},\n'
        )