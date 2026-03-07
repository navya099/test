import math

from bve.pole_builder.base_pole_builder import BasePoleBuilder
from utils.pole_dimention_finder import PoleDimensionFinder


class PIPEPoleBuilder(BasePoleBuilder):
    """
    강관주 빌더
    Attributes:
        length: 기둥 전체높이 예 9m
        diameter: 기둥 직경 267.4mm
        pipe_r: 파이프 반지름
    """
    def __init__(self, length, diameter):
        super().__init__(length, diameter)
        self.pipe_r = self.diameter / 2

    def build(self):
        self.build_colum(self.length, self.diameter, buttom_y=0.381) #기둥 본체
        ring_width = self.cal_ring_width()
        self.build_ring(0.032, ring_width, buttom_y=0.381) #하단 간판
        dimension_str = PoleDimensionFinder.get_pole_type_by_dimension('PIPE', self.diameter)
        self.save_text(f'c:/temp/강관주_{dimension_str}_{self.length}m.csv')
        return self.path

    def build_colum(self, height, diameter, buttom_y):
        """6각 기둥 생성 메서드
        Args:
            buttom_y: 기둥 바닥 높이
            height: 기둥 높이
            diameter: 기둥 지름
        """
        self.text.append(';기둥\n')
        self._build_header()  # 헤더생성
        radius = diameter / 2
        bot_y = buttom_y
        top_y = height - bot_y

        # 버텍스 x,z,nx,ny,nz
        coords = self.get_coords_and_normals(radius, 6)

        (x0, z0, nx0, ny0, nz0) = coords[0]
        (x1, z1, nx1, ny1, nz1) = coords[1]
        (x2, z2, nx2, ny2, nz2) = coords[2]
        (x3, z3, nx3, ny3, nz3) = coords[3]
        (x4, z4, nx4, ny4, nz4) = coords[4]
        (x5, z5, nx5, ny5, nz5) = coords[5]

        # 버텍스 추가
        self.text.append(f'AddVertex, {x0}, {-bot_y}, {z0}, {nx0}, {ny0}, {nz0},\n')
        self.text.append(f'AddVertex, {x5}, {top_y}, {z5}, {nx5}, {ny5}, {nz5},\n')
        self.text.append(f'AddVertex, {x5}, {-bot_y}, {z5}, {nx5}, {ny5}, {nz5},\n')
        self.text.append(f'AddVertex, {x0}, {top_y}, {z0}, {nx0}, {ny0}, {nz0},\n')
        self.text.append(f'AddVertex, {x4}, {-bot_y}, {z4}, {nx4}, {ny4}, {nz4},\n')
        self.text.append(f'AddVertex, {x4}, {top_y}, {z4}, {nx4}, {ny4}, {nz4},\n')
        self.text.append(f'AddVertex, {x3}, {top_y}, {z3}, {nx3}, {ny3}, {nz3},\n')
        self.text.append(f'AddVertex, {x3}, {-bot_y}, {z3}, {nx3}, {ny3}, {nz3},\n')
        self.text.append(f'AddVertex, {x2}, {top_y}, {z2}, {nx2}, {ny2}, {nz2},\n')
        self.text.append(f'AddVertex, {x2}, {-bot_y}, {z2}, {nx2}, {ny2}, {nz2},\n')
        self.text.append(f'AddVertex, {x2}, {top_y}, {z2}, {nx2}, {ny2}, {nz2},\n')
        self.text.append(f'AddVertex, {x1}, {-bot_y}, {z1}, {nx1}, {ny1}, {nz1},\n')
        self.text.append(f'AddVertex, {x2}, {-bot_y}, {z2}, {nx2}, {ny2}, {nz2},\n')
        self.text.append(f'AddVertex, {x1}, {top_y}, {z1}, {nx1}, {ny1}, {nz1},\n')

        # face 생성
        self.text.append("AddFace, 0, 2, 1,\n")
        self.text.append("AddFace, 1, 3, 0,\n")
        self.text.append("AddFace, 1, 2, 4,\n")
        self.text.append("AddFace, 4, 5, 1,\n")
        self.text.append("AddFace, 6, 5, 4,\n")
        self.text.append("AddFace, 4, 7, 6,\n")
        self.text.append("AddFace, 8, 6, 7,\n")
        self.text.append("AddFace, 7, 9, 8,\n")
        self.text.append("AddFace, 10, 12, 11,\n")
        self.text.append("AddFace, 11, 13, 10,\n")
        self.text.append("AddFace, 11, 0, 3,\n")
        self.text.append("AddFace, 3, 13, 11,\n")

        # 텍스쳐 생성
        self.text.append('LoadTexture, Metal_Corrogated_Shiny.jpg,\n')
        self.text.append('SetColor, 255, 255, 255, 255,\n')

        # 텍스쳐 좌표 생성
        self.text.append("SetTextureCoordinates, 0, 0.333, -0.004,\n")
        self.text.append("SetTextureCoordinates, 1, 0.5, 1.0,\n")
        self.text.append("SetTextureCoordinates, 2, 0.5, -0.004,\n")
        self.text.append("SetTextureCoordinates, 3, 0.333, 1.0,\n")
        self.text.append("SetTextureCoordinates, 4, 0.667, -0.004,\n")
        self.text.append("SetTextureCoordinates, 5, 0.667, 1.0,\n")
        self.text.append("SetTextureCoordinates, 6, 0.833, 1.0,\n")
        self.text.append("SetTextureCoordinates, 7, 0.833, -0.004,\n")
        self.text.append("SetTextureCoordinates, 8, 1.0, 1.0,\n")
        self.text.append("SetTextureCoordinates, 9, 1.0, -0.004,\n")
        self.text.append("SetTextureCoordinates, 10, 0.0, 1.0,\n")
        self.text.append("SetTextureCoordinates, 11, 0.167, -0.004,\n")
        self.text.append("SetTextureCoordinates, 12, 0.0, -0.004,\n")
        self.text.append("SetTextureCoordinates, 13, 0.167, 1.0,\n")

        # 상부 파이프 캡
        self.build_circle(radius, top_y)

    def build_circle(self, radius, y_coord):
        """6각 평면 생성"""
        self.text.append(';파이프캡\n')
        self._build_header()
        # 버텍스 x,z,nx,ny,nz
        coords = self.get_coords_and_normals(radius, 6)

        (x0, z0, nx0, ny0, nz0) = coords[0]
        (x1, z1, nx1, ny1, nz1) = coords[1]
        (x2, z2, nx2, ny2, nz2) = coords[2]
        (x3, z3, nx3, ny3, nz3) = coords[3]
        (x4, z4, nx4, ny4, nz4) = coords[4]
        (x5, z5, nx5, ny5, nz5) = coords[5]

        # 버텍스 생성
        self.text.append(f'AddVertex, {x4}, {y_coord}, {z4}, 0.0, 1.0, 0.0,\n')
        self.text.append(f'AddVertex, {x2}, {y_coord}, {z2}, 0.0, 1.0, 0.0,\n')
        self.text.append(f'AddVertex, {x3}, {y_coord}, {z3}, 0.0, 1.0, 0.0,\n')
        self.text.append(f'AddVertex, {x5}, {y_coord}, {z5}, 0.0, 1.0, 0.0,\n')
        self.text.append(f'AddVertex, {x1}, {y_coord}, {z1}, 0.0, 1.0, 0.0,\n')
        self.text.append(f'AddVertex, {x0}, {y_coord}, {z0}, 0.0, 1.0, 0.0,\n')

        # face 생성
        self.text.append("AddFace, 0, 2, 1,\n")
        self.text.append("AddFace, 1, 3, 0,\n")
        self.text.append("AddFace, 1, 4, 3,\n")
        self.text.append("AddFace, 4, 5, 3,\n")
        self.text.append("SetColor, 255, 255, 255, 255,\n")

        # 텍스쳐 생성
        self.text.append('LoadTexture, Metal_Corrogated_Shiny.jpg,\n')
        self.text.append('SetTextureCoordinates, 0, 0.134, 1.0,\n')
        self.text.append('SetTextureCoordinates, 1, 0.134, 0.537,\n')
        self.text.append('SetTextureCoordinates, 2, 0.0, 0.768,\n')
        self.text.append('SetTextureCoordinates, 3, 0.401, 1.0,\n')
        self.text.append('SetTextureCoordinates, 4, 0.401, 0.537,\n')
        self.text.append('SetTextureCoordinates, 5, 0.535, 0.768,\n')

    def build_ring(self, height, diameter, buttom_y=0.381):
        #파이프 하부 강판 생성
        self.build_colum(height, diameter, buttom_y)

    def get_x_z(self, radius, angle: float):
        """원 테셀레이션 다각형 좌표 반환(x,z)평면좌표계"""
        x = radius * math.cos(math.radians(angle))
        z = radius * math.sin(math.radians(angle))
        return x,z

    def get_nx_nz(self ,angle: float):
        """노말벡터 계산"""
        nx = math.cos(math.radians(angle))
        ny = 0
        nz = math.sin(math.radians(angle))
        return nx, ny, nz

    def get_coords_and_normals(self, radius: float, side: int):
        result = []
        step = 360 / side

        for i in range(side):
            angle = i * step
            x, z = self.get_x_z(radius, angle)
            nx, ny, nz = self.get_nx_nz(angle)
            result.append((x, z, nx, ny, nz))

        return result

    def cal_ring_width(self):
        if 0.2674 >= self.diameter >= 0.3556:
            ring_width = 0.65
        elif 0.3556 > self.diameter > 0.5:
            ring_width = 0.85
        else:
            ring_width = 1
            return  ring_width