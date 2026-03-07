import math

from bve.beam_builder.base_builder import BaseBeamBuilder


class TRUSSBeamBuilder(BaseBeamBuilder):
    """
    트러스빔 빌더
    Attributes:
        length: 빔 전체길이 l
    """
    def __init__(self, length):
        super().__init__(length)

    def build(self):
        self.build_gueset_plate()
        self._build_header()
        self.build_beam_body() #빔 본체
        self.build_gueset_plate(dx=self.length,rotate_180=True)
        self.save_text(f'D:/BVE/루트/Railway/Object/temp/트러스빔-{self.length}m.csv')
        return self.path

    def build_beam_body(self):

        bottom = 7.36
        top = 7.96
        half = 0.138
        gasset_offset = 0.235
        x0 = 0.0
        x1 = self.length
        half_length = self.length / 2
        t_coord = TRUSSBeamBuilder.calc_u_coord(half_length)
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
                          f'SetTextureCoordinates, 4, {t_coord}, -41.0,\n',
                          f'SetTextureCoordinates, 5, -1.0, -42.0,\n',
                          f'SetTextureCoordinates, 6, -1.0, -41.0,\n',
                          f'SetTextureCoordinates, 7, {t_coord}, -42.0,\n',
                          f'SetTextureCoordinates, 8, {t_coord}, -41.0,\n',
                          f'SetTextureCoordinates, 9, -1.0, -40.0,\n',
                          f'SetTextureCoordinates, 10, {t_coord}, -40.0,\n',
                          f'SetTextureCoordinates, 11, -1.0, -41.0,\n',
                          f'SetTextureCoordinates, 12, -1.0, -41.0,\n',
                          f'SetTextureCoordinates, 13, {t_coord}, -40.0,\n',
                          f'SetTextureCoordinates, 14, -1.0, -40.0,\n',
                          f'SetTextureCoordinates, 15, {t_coord}, -41.0,\n',
                          f'SetTextureCoordinates, 16, {t_coord}, -42.0,\n',
                          f'SetTextureCoordinates, 17, -1.0, -41.0,\n',
                          f'SetTextureCoordinates, 18, -1.0, -42.0,\n',
                          f'SetTextureCoordinates, 19, {t_coord}, -41.0,\n',
                          f'SetTextureCoordinates, 20, 2.339, 0.936,\n',
                          f'SetTextureCoordinates, 21, 2.197, -2.219,\n',
                          f'SetTextureCoordinates, 22, 2.197, 0.936,\n',
                          f'SetTextureCoordinates, 23, 2.339, -2.219,\n',
                          f'SetTextureCoordinates, 24, {t_coord}, -41.0,\n',
                          f'SetTextureCoordinates, 25, -1.0, -42.0,\n',
                          f'SetTextureCoordinates, 26, -1.0, -41.0,\n',
                          f'SetTextureCoordinates, 27, {t_coord}, -42.0,\n',
                          f'SetTextureCoordinates, 28, {t_coord}, -41.0,\n',
                          f'SetTextureCoordinates, 29, -1.0, -40.0,\n',
                          f'SetTextureCoordinates, 30, {t_coord}, -40.0,\n',
                          f'SetTextureCoordinates, 31, -1.0, -41.0,\n',
                          f'SetTextureCoordinates, 32, -1.0, -41.0,\n',
                          f'SetTextureCoordinates, 33, {t_coord}, -40.0,\n',
                          f'SetTextureCoordinates, 34, -1.0, -40.0,\n',
                          f'SetTextureCoordinates, 35, {t_coord}, -41.0,\n',
                          f'SetTextureCoordinates, 36, {t_coord}, -42.0,\n',
                          f'SetTextureCoordinates, 37, -1.0, -41.0,\n',
                          f'SetTextureCoordinates, 38, -1.0, -42.0,\n',
                          f'SetTextureCoordinates, 39, {t_coord}, -41.0,\n', ])

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



    def _current_vertex_index(self):
        count = 0
        for line in self.text:
            if line.startswith("AddVertex"):
                count += 1
        return count


    @staticmethod
    def calc_u_coord(length, tex_length=1.936):
        """
        모델 길이에 따른 U 좌표 계산
        :param length: 모델 길이 (m)
        :param tex_length: 텍스처 기준 길이 (m), 기본값 1.936
        :return: U 좌표 값
        """
        return (length / tex_length) - 1