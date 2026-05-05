import math

class TempletePoleBuilder:
    """
    기둥 템플릿 빌더
    Attributes:
        length: 기둥 전체높이 예 9m
        diameter: 기둥 직경 267.4mm
        pipe_r: 파이프 반지름
    """
    def __init__(self, length, diameter):
        self.length = length #
        self.diameter = diameter
        self.pipe_r = self.diameter / 2
        self.text = []
        self.path = ''
    def build(self):
        self.build_colum(self.length, self.diameter, buttom_y=0) #기둥 본체
        self.build_ring(0.032, 0.65, buttom_y=0) #하단 링
        self.save_text()
        return self.path

    def _build_header(self):
        self.text.append(';by BeamAsemmbler Templete created')
        self.text.append('CreateMeshBuilder,')

    def build_colum(self, height, diameter, buttom_y):
        """6각 기둥 생성 메서드
        Args:
            buttom_y: 기둥 바닥 높이
            height: 기둥 높이
            diameter: 기둥 지름

        """
        self.text.append(f';기둥\n')
        self._build_header() #헤더생성
        radius = diameter / 2
        bot_y = buttom_y
        top_y = height - bot_y

        #버텍스 x,z,nx,ny,nz
        coords = self.get_coords_and_normals(radius, 6)

        (x0, z0, nx0, ny0, nz0) = coords[0]
        (x1, z1, nx1, ny1, nz1) = coords[1]
        (x2, z2, nx2, ny2, nz2) = coords[2]
        (x3, z3, nx3, ny3, nz3) = coords[3]
        (x4, z4, nx4, ny4, nz4) = coords[4]
        (x5, z5, nx5, ny5, nz5) = coords[5]

        self.text.extend([
        f'AddVertex, {x0}, {-bot_y}, {z0}, {nx0}, {ny0}, {nz0},',
        f'AddVertex, {x5}, {top_y}, {z5}, {nx5}, {ny5}, {nz5},',
        f'AddVertex, {x5}, {-bot_y}, {z5}, {nx5}, {ny5}, {nz5},',
        f'AddVertex, {x0}, {top_y}, {z0}, {nx0}, {ny0}, {nz0},' ,#최상단 노벌벡터 고정
        f'AddVertex, {x4}, {-bot_y}, {z4}, {nx4}, {ny4}, {nz4},',
        f'AddVertex, {x4}, {top_y}, {z4}, {nx4}, {ny4}, {nz4},',
        f'AddVertex, {x3}, {top_y}, {z3}, {nx3}, {ny3}, {nz3},',
        f'AddVertex, {x3}, {-bot_y}, {z3}, {nx3}, {ny3}, {nz3},',
        f'AddVertex, {x2}, {top_y}, {z2}, {nx2}, {ny2}, {nz2},',
        f'AddVertex, {x2}, {-bot_y}, {z2}, {nx2}, {ny2}, {nz2},',
        f'AddVertex, {x2}, {top_y}, {z2}, {nx2}, {ny2}, {nz2},',
        f'AddVertex, {x1}, {-bot_y}, {z1}, {nx1}, {ny1}, {nz1},',
        f'AddVertex, {x2}, {-bot_y}, {z2}, {nx2}, {ny2}, {nz2},',
        f'AddVertex, {x1}, {top_y}, {z1}, {nx1}, {ny1}, {nz1},',
        ])
        #face생성
        self.text.extend([
            "AddFace, 0, 2, 1,",
            "AddFace, 1, 3, 0,",
            "AddFace, 1, 2, 4,",
            "AddFace, 4, 5, 1,",
            "AddFace, 6, 5, 4,",
            "AddFace, 4, 7, 6,",
            "AddFace, 8, 6, 7,",
            "AddFace, 7, 9, 8,",
            "AddFace, 10, 12, 11,",
            "AddFace, 11, 13, 10,",
            "AddFace, 11, 0, 3,",
            "AddFace, 3, 13, 11,",
        ])

        #텍스쳐 생성
        self.text.append(f'LoadTexture, Metal_Corrogated_Shiny.jpg,')
        self.text.append(f'SetColor, 255, 255, 255, 255,')
        #텍스쳐 좌표 생성
        self.text.extend([
            "SetTextureCoordinates, 0, 0.333, -0.004,",
            "SetTextureCoordinates, 1, 0.5, 1.0,",
            "SetTextureCoordinates, 2, 0.5, -0.004,",
            "SetTextureCoordinates, 3, 0.333, 1.0,",
            "SetTextureCoordinates, 4, 0.667, -0.004,",
            "SetTextureCoordinates, 5, 0.667, 1.0,",
            "SetTextureCoordinates, 6, 0.833, 1.0,",
            "SetTextureCoordinates, 7, 0.833, -0.004,",
            "SetTextureCoordinates, 8, 1.0, 1.0,",
            "SetTextureCoordinates, 9, 1.0, -0.004,",
            "SetTextureCoordinates, 10, 0.0, 1.0,",
            "SetTextureCoordinates, 11, 0.167, -0.004,",
            "SetTextureCoordinates, 12, 0.0, -0.004,",
            "SetTextureCoordinates, 13, 0.167, 1.0,\n",
        ])
        #상부 파이프 캡
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
        self.text.extend([
            f'AddVertex, {x4}, {y_coord}, {z4}, 0.0, 1.0, 0.0,',
            f'AddVertex, {x2}, {y_coord}, {z2}, 0.0, 1.0, 0.0,',
            f'AddVertex, {x3}, {y_coord}, {z3}, 0.0, 1.0, 0.0,',
            f'AddVertex, {x5}, {y_coord}, {z5}, 0.0, 1.0, 0.0,',
            f'AddVertex, {x1}, {y_coord}, {z1}, 0.0, 1.0, 0.0,',
            f'AddVertex, {x0}, {y_coord}, {z0}, 0.0, 1.0, 0.0,',
        ])
        # face생성
        self.text.extend([
            "AddFace, 0, 2, 1,",
            "AddFace, 1, 3, 0,",
            "AddFace, 1, 4, 3,",
            "AddFace, 4, 5, 3,",
            "SetColor, 255, 255, 255, 255,"

        ])
        #텍스쳐 생성
        self.text.extend([
            f'LoadTexture, Metal_Corrogated_Shiny.jpg,',
            f'SetTextureCoordinates, 0, 0.134, 1.0,',
            f'SetTextureCoordinates, 1, 0.134, 0.537,',
            f'SetTextureCoordinates, 2, 0.0, 0.768,',
            f'SetTextureCoordinates, 3, 0.401, 1.0,',
            f'SetTextureCoordinates, 4, 0.401, 0.537,',
            f'SetTextureCoordinates, 5, 0.535, 0.768,\n'
        ])

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

    def save_text(self):
        self.path = f'c:/temp/custom_pole_{self.length}m.csv'
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.text))