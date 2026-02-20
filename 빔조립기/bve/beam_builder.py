import math

class TempleteBeamBuilder:
    """
    빔 템플릿 빌더(트러스,트러스라멘)
    Attributes:
        length: 빔 전체길이 l
    """
    def __init__(self, length):
        self.length = length #
        self.text = []
        self.path = ''
    def build(self):
        self.build_gueset_plate()
        self._build_header()
        self.build_beam_body() #빔 본체
        self.build_gueset_plate(dx=self.length,rotate_180=True)
        self.save_text()

        return self.path

    def _build_header(self):
        self.text.append('\n;by BeamAsemmbler Templete created\n')
        self.text.append('CreateMeshBuilder,\n')

    def build_beam_body(self):

        bottom = 7.36
        top = 7.96
        half = 0.138
        gasset_offset = 0.235
        x0 = 0.0
        x1 = self.length
        half_length = self.length / 2
        self.text.extend([f'AddVertex, {half_length}, {bottom}, {half}, 1.0, 0.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, -{half}, 1.0, 0.0, 0.0,\n',
                         f'AddVertex, {half_length}, {bottom}, -{half}, 1.0, 0.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, {half}, 1.0, 0.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, -{half}, 0.0, 1.0, 0.0,\n',
                         f'AddVertex, -{gasset_offset}, {top}, {half}, 0.0, 1.0, 0.0,\n',
                         f'AddVertex, -{gasset_offset}, {top}, -{half}, 0.0, 1.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, {half}, 0.0, 1.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, -{half}, 0.0, 0.0, -1.0,\n',
                         f'AddVertex, -{gasset_offset}, {bottom}, -{half}, 0.0, 0.0, -1.0,\n',
                         f'AddVertex, {half_length}, {bottom}, -{half}, 0.0, 0.0, -1.0,\n',
                         f'AddVertex, -{gasset_offset}, {top}, -{half}, 0.0, 0.0, -1.0,\n',
                         f'AddVertex, -{gasset_offset}, {top}, {half}, 0.0, 0.0, 1.0,\n',
                         f'AddVertex, {half_length}, {bottom}, {half}, 0.0, 0.0, 1.0,\n',
                         f'AddVertex, -{gasset_offset}, {bottom}, {half}, 0.0, 0.0, 1.0,\n',
                         f'AddVertex, {half_length}, {top}, {half}, 0.0, 0.0, 1.0,\n',
                         f'AddVertex, {half_length}, {bottom}, {half}, 0.0, -1.0, 0.0,\n',
                         f'AddVertex, -{gasset_offset}, {bottom}, -{half}, 0.0, -1.0, 0.0,\n',
                         f'AddVertex, -{gasset_offset}, {bottom}, {half}, 0.0, -1.0, 0.0,\n',
                         f'AddVertex, {half_length}, {bottom}, -{half}, 0.0, -1.0, 0.0,\n',
                         f'AddVertex, {half_length}, {bottom}, {half}, -1.0, 0.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, -{half}, -1.0, 0.0, 0.0,\n',
                         f'AddVertex, {half_length}, {bottom}, -{half}, -1.0, 0.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, {half}, -1.0, 0.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, -{half}, 0.0, 1.0, 0.0,\n',
                         f'AddVertex, {x1 + gasset_offset}, {top}, {half}, 0.0, 1.0, 0.0,\n',
                         f'AddVertex, {x1 + gasset_offset}, {top}, -{half}, 0.0, 1.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, {half}, 0.0, 1.0, 0.0,\n',
                         f'AddVertex, {half_length}, {top}, -{half}, 0.0, 0.0, -1.0,\n',
                         f'AddVertex, {x1 + gasset_offset}, {bottom}, -{half}, 0.0, 0.0, -1.0,\n',
                         f'AddVertex, {half_length}, {bottom}, -{half}, 0.0, 0.0, -1.0,\n',
                         f'AddVertex, {x1 + gasset_offset}, {top}, -{half}, 0.0, 0.0, -1.0,\n',
                         f'AddVertex, {x1 + gasset_offset}, {top}, {half}, 0.0, 0.0, 1.0,\n',
                         f'AddVertex, {half_length}, {bottom}, {half}, 0.0, 0.0, 1.0,\n',
                         f'AddVertex, {x1 + gasset_offset}, {bottom}, {half}, 0.0, 0.0, 1.0,\n',
                         f'AddVertex, {half_length}, {top}, {half}, 0.0, 0.0, 1.0,\n',
                         f'AddVertex, {half_length}, {bottom}, {half}, 0.0, -1.0, 0.0,\n',
                         f'AddVertex, {x1 + gasset_offset}, {bottom}, -{half}, 0.0, -1.0, 0.0,\n',
                         f'AddVertex, {x1 + gasset_offset}, {bottom}, {half}, 0.0, -1.0, 0.0,\n',
                         f'AddVertex, {half_length}, {bottom}, -{half}, 0.0, -1.0, 0.0,\n',
                         f'AddFace, 0, 2, 1,\n',
                         f'AddFace, 1, 3, 0,\n',
                         f'AddFace, 4, 6, 5,\n',
                         f'AddFace, 5, 7, 4,\n',
                         f'AddFace, 8, 10, 9,\n',
                         f'AddFace, 9, 11, 8,\n',
                         f'AddFace, 12, 14, 13,\n',
                         f'AddFace, 13, 15, 12,\n',
                         f'AddFace, 16, 18, 17,\n',
                         f'AddFace, 17, 19, 16,\n',
                         f'AddFace, 22, 20, 21,\n',
                         f'AddFace, 23, 21, 20,\n',
                         f'AddFace, 26, 24, 25,\n',
                         f'AddFace, 27, 25, 24,\n',
                         f'AddFace, 30, 28, 29,\n',
                         f'AddFace, 31, 29, 28,\n',
                         f'AddFace, 34, 32, 33,\n',
                         f'AddFace, 35, 33, 32,\n',
                         f'AddFace, 38, 36, 37,\n',
                         f'AddFace, 39, 37, 36,\n',
                         f'LoadTexture, 4각트러스빔.png,\n',
                         f'SetColor, 255, 255, 255, 255,\n'
                         f'SetTextureCoordinates, 0, 2.339, 0.936,\n',
                         f'SetTextureCoordinates, 1, 2.197, -2.219,\n',
                         f'SetTextureCoordinates, 2, 2.197, 0.936,\n',
                         f'SetTextureCoordinates, 3, 2.339, -2.219,\n',
                         f'SetTextureCoordinates, 4, 1.198, -41.0,\n',
                         f'SetTextureCoordinates, 5, -1.0, -42.0,\n',
                         f'SetTextureCoordinates, 6, -1.0, -41.0,\n',
                         f'SetTextureCoordinates, 7, 1.198, -42.0,\n',
                         f'SetTextureCoordinates, 8, 1.198, -41.0,\n',
                         f'SetTextureCoordinates, 9, -1.0, -40.0,\n',
                         f'SetTextureCoordinates, 10, 1.198, -40.0,\n',
                         f'SetTextureCoordinates, 11, -1.0, -41.0,\n',
                         f'SetTextureCoordinates, 12, -1.0, -41.0,\n',
                         f'SetTextureCoordinates, 13, 1.198, -40.0,\n',
                         f'SetTextureCoordinates, 14, -1.0, -40.0,\n',
                         f'SetTextureCoordinates, 15, 1.198, -41.0,\n',
                         f'SetTextureCoordinates, 16, 1.198, -42.0,\n',
                         f'SetTextureCoordinates, 17, -1.0, -41.0,\n',
                         f'SetTextureCoordinates, 18, -1.0, -42.0,\n',
                         f'SetTextureCoordinates, 19, 1.198, -41.0,\n',
                         f'SetTextureCoordinates, 20, 2.339, 0.936,\n',
                         f'SetTextureCoordinates, 21, 2.197, -2.219,\n',
                         f'SetTextureCoordinates, 22, 2.197, 0.936,\n',
                         f'SetTextureCoordinates, 23, 2.339, -2.219,\n',
                         f'SetTextureCoordinates, 24, 1.198, -41.0,\n',
                         f'SetTextureCoordinates, 25, -1.0, -42.0,\n',
                         f'SetTextureCoordinates, 26, -1.0, -41.0,\n',
                         f'SetTextureCoordinates, 27, 1.198, -42.0,\n',
                         f'SetTextureCoordinates, 28, 1.198, -41.0,\n',
                         f'SetTextureCoordinates, 29, -1.0, -40.0,\n',
                         f'SetTextureCoordinates, 30, 1.198, -40.0,\n',
                         f'SetTextureCoordinates, 31, -1.0, -41.0,\n',
                         f'SetTextureCoordinates, 32, -1.0, -41.0,\n',
                         f'SetTextureCoordinates, 33, 1.198, -40.0,\n',
                         f'SetTextureCoordinates, 34, -1.0, -40.0,\n',
                         f'SetTextureCoordinates, 35, 1.198, -41.0,\n',
                         f'SetTextureCoordinates, 36, 1.198, -42.0,\n',
                         f'SetTextureCoordinates, 37, -1.0, -41.0,\n',
                         f'SetTextureCoordinates, 38, -1.0, -42.0,\n',
                         f'SetTextureCoordinates, 39, 1.198, -41.0,\n',])

    def build_gueset_plate(self, dx=0, dy=0, dz=0, rotate_180=False):
        with open('c:/temp/gausset_plate.csv', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith("AddVertex"):
                parts = line.split(",")

                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])

                # 🔁 180도 회전
                if rotate_180:
                    x = -x
                    z = -z

                # 📍 이동
                x += dx
                y += dy
                z += dz

                parts[1] = f" {round(x, 3)}"
                parts[2] = f" {round(y, 3)}"
                parts[3] = f" {round(z, 3)}"

                self.text.append(",".join(parts))
            else:
                self.text.append(line)

    def save_text(self):
        self.path = f'c:/temp/custom_beam_{self.length}m.csv'
        with open(self.path, 'w', encoding='utf-8') as f:
            f.writelines(self.text)

    def _current_vertex_index(self):
        count = 0
        for line in self.text:
            if line.startswith("AddVertex"):
                count += 1
        return count

    def v(self, x, y, z, nx, ny, nz):
        self.text.append(
            f'AddVertex, {x:.6f}, {y:.6f}, {z:.6f}, {nx}, {ny}, {nz},'
        )