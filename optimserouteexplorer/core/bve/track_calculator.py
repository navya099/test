import math
from core.util import Vector2
from core.bve.curveblock import Curveblock
from core.bve.pitchblock import PitchBlock
from core.util import Vector3
import numpy as np

class TrackCalculator:
    def __init__(self, curve_blocks: list[Curveblock],pitch_blocks: list[PitchBlock] ,interval: float = 25):
        self.interval = interval
        self.data = []
        self.curves = curve_blocks
        self.pitchs = pitch_blocks


    def calculate_block(self, direction: float = 0.0, position: Vector3 = Vector3(x=0.0, y=0.0, z=0.0)):

        #direction을 벡터2로 변환
        direction = Vector2(math.cos(direction), math.sin(direction))

        for curve, grade in zip(self.curves, self.pitchs):
            a = 0.0
            c = self.interval
            h = 0.0
            radius = curve.radius
            pitch = grade.pitch

            self.data.append(position.copy())
            c,h = self._calc_curve_pitch(radius, pitch, direction)


            position.x += direction.x * c
            position.y += direction.y * c
            position.z += h

            if a != 0.0:
                direction.rotate(math.cos(-a), math.sin(-a))

    def _calc_curve_pitch(self, radius, pitch, direction):
        d = self.interval
        h = 0.0
        c = d
        a = 0.0

        if radius != 0.0 and pitch != 0.0:
            s = d / math.sqrt(1.0 + pitch * pitch)
            h = s * pitch
            b = s / abs(radius)
            c = math.sqrt(2.0 * radius * radius * (1.0 - math.cos(b)))
            a = 0.5 * np.sign(radius) * b
        elif radius != 0.0:
            b = d / abs(radius)
            c = math.sqrt(2.0 * radius * radius * (1.0 - math.cos(b)))
            a = 0.5 * np.sign(radius) * b
        elif pitch != 0.0:
            c = d / math.sqrt(1.0 + pitch * pitch)
            h = c * pitch

        if a != 0.0:
            direction.rotate(math.cos(-a), math.sin(-a))

        return c, h

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            for block in self.data:
                f.write(f"{block.x},{block.y},{block.z}\n")