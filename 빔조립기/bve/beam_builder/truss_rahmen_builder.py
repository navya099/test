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
        self.build_gueset_plate()
        self._build_header()
        self.build_beam_body() #빔 본체
        self.build_gueset_plate(dx=self.length,rotate_180=True)
        self.save_text(f'c:/temp/트러스라멘빔_{self.length}m.csv')

        return self.path

    def build_beam_body(self, dx=0, dy=0, dz=0, rotate_180=False):
        with open('c:/temp/truss_rahmen_middle.csv', 'r', encoding='utf-8') as f:
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

    def build_gueset_plate(self, dx=0, dy=0, dz=0, rotate_180=False):
        with open('c:/temp/truss_rahmen_gausset_plate.csv', 'r', encoding='utf-8') as f:
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