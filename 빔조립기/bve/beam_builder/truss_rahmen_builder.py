import math

from bve.beam_builder.base_builder import BaseBeamBuilder


class TrussRahmenBeamBuilder(BaseBeamBuilder):
    """
    트러스라멘빌더
    Attributes:
        length: 빔 전체길이 l
    """
    def __init__(self, length):
        super().__init__(length)

    def build(self):
        self.build_gueset_plate(direction='L')
        self._build_header()
        self.build_beam_body() #빔 본체
        self.build_gueset_plate(dx=self.length,direction='R')
        self.save_text(f'c:/temp/트러스라멘빔_{self.length}m.csv')

        return self.path

    def build_beam_body(self):
        #정면
        x = self.length - 4.73
        self._build_header()
        self.v(x, 7.315 + 1, -0.225, 0.0, 0.0, -1.0)
        self.v(4.73, 7.315, -0.225, 0.0, 0.0, -1.0)
        self.v(x, 7.315, -0.225, 0.0, 0.0, -1.0)
        self.v(4.73, 7.315 + 1, -0.225, 0.0, 0.0, -1.0)
        self.addface(0,2,1,True)
        self.addface(1, 3, 0, True)
        self.load_texture('트러스라멘빔M.png')
        self.set_color(255, 255, 255, 255)
        self.set_texture_coordinates(0, x, 0)
        self.set_texture_coordinates(1, 1, 1)
        self.set_texture_coordinates(2, x, 1)
        self.set_texture_coordinates(3, 1, 0)

        #후면
        self._build_header()
        self.v(x, 7.315 + 1, 0.225, 0.0, 0.0, -1.0)
        self.v(4.73, 7.315, 0.225, 0.0, 0.0, -1.0)
        self.v(x, 7.315, 0.225, 0.0, 0.0, -1.0)
        self.v(4.73, 7.315 + 1, 0.225, 0.0, 0.0, -1.0)

        self.addface(0, 2, 1, True)
        self.addface(1, 3, 0, True)
        self.load_texture('트러스라멘빔M.png')
        self.set_color(255, 255, 255, 255)
        self.set_texture_coordinates(0, x, 0)
        self.set_texture_coordinates(1, 1, 1)
        self.set_texture_coordinates(2, x, 1)
        self.set_texture_coordinates(3, 1, 0)

        #top
        self._build_header()
        self.v(x, 7.315 + 1, -0.225, 0.0, 1.0, 0)
        self.v(4.73, 7.315 + 1, 0.225, 0.0, 1.0, 0)
        self.v(4.73, 7.315 + 1, -0.225, 0.0, 1, 0)
        self.v(x, 7.315 + 1, 0.225, 0.0, 1, 0)

        self.addface(0, 2, 1, True)
        self.addface(1, 3, 0, True)
        self.load_texture('트러스라멘빔TOP.png')
        self.set_color(255, 255, 255, 255)
        self.set_texture_coordinates(0, 0.28 + x, 1)
        self.set_texture_coordinates(1, -0.8, 0)
        self.set_texture_coordinates(2, -0.8, 1)
        self.set_texture_coordinates(3, 0.28 + x, 0)

        #buttom
        self._build_header()
        self.v(x, 7.315, -0.225, 0.0, 1.0, 0)
        self.v(4.73, 7.315, 0.225, 0.0, 1.0, 0)
        self.v(4.73, 7.315, -0.225, 0.0, 1, 0)
        self.v(x, 7.315, 0.225, 0.0, 1, 0)

        self.addface(0, 2, 1, True)
        self.addface(1, 3, 0, True)
        self.load_texture('트러스라멘빔TOP.png')
        self.set_color(255, 255, 255, 255)
        self.set_texture_coordinates(0, 0.28 + x, 1)
        self.set_texture_coordinates(1, -0.8, 0)
        self.set_texture_coordinates(2, -0.8, 1)
        self.set_texture_coordinates(3, 0.28 + x, 0)

    def build_gueset_plate(self, dx=0, dy=0, dz=0, direction=None):
        if direction == 'L':
            fname = 'truss_rahmen_gausset_plate_L'
        else:
            fname = 'truss_rahmen_gausset_plate_R'
        with open(f'c:/temp/{fname}.csv', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith("AddVertex"):
                parts = line.split(",")

                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])

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