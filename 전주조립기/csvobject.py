import math

class CSVObject:
    """
    OPENBVE CSV오브젝트 조작용 클래스
    Attributes:
        lines: 대상 줄 리스트
    """
    def __init__(self, lines):
        self.lines = lines

    def translate(self, dx=0.0, dy=0.0, dz=0.0) -> list:
        """
        CSV오브젝트 Translate
        :param dx:
        :param dy:
        :param dz:
        :return: 새 줄
        """
        new_lines = []
        for line in self.lines:
            if line.strip().startswith('AddVertex'):
                parts = line.strip().split(',')
                try:
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    z = float(parts[3].strip())
                    # 좌표 이동
                    parts[1] = str(x + dx)
                    parts[2] = str(y + dy)
                    parts[3] = str(z + dz)
                    new_line = ','.join(parts) + '\n'
                    new_lines.append(new_line)
                except ValueError:
                    new_lines.append(line)  # 변환 실패하면 원본 그대로
            else:
                new_lines.append(line)
        return new_lines

    def scale(self, sx=1.0, sy=1.0, sz=1.0):
        """
        CSV오브젝트 Scale
        :param sx:
        :param sy:
        :param sz:
        :return:
        """
        new_lines = []
        for line in self.lines:
            if line.strip().startswith('AddVertex'):
                parts = line.strip().split(',')
                parts[1] = str(float(parts[1]) * sx)
                parts[2] = str(float(parts[2]) * sy)
                parts[3] = str(float(parts[3]) * sz)
                new_lines.append(','.join(parts))
            else:
                new_lines.append(line)
        self.lines = new_lines
        return self.lines

    def rotate(self, axis_x=0, axis_y=0, axis_z=0, angle=0.0):
        """
        CSV오브젝트 Rotate
        :param axis_x:
        :param axis_y:
        :param axis_z:
        :param angle:
        :return:
        """
        new_lines = []
        for line in self.lines:
            if line.strip().startswith('AddVertex'):
                new_lines.append(self._rotate_line(line, axis_x, axis_y, axis_z, angle))
            else:
                new_lines.append(line)
        self.lines = new_lines
        return self.lines

    @staticmethod
    def _rotate_line(line, x, y, z, angle):
        if 'AddVertex' not in line:
            return line

        # 좌표 추출
        parts = line.strip().split(',')
        vx, vy, vz = float(parts[1]), float(parts[2]), float(parts[3])

        # 회전축 정규화
        length = math.sqrt(x ** 2 + y ** 2 + z ** 2)
        if length == 0:
            x, y, z = 1, 0, 0
        else:
            x, y, z = x / length, y / length, z / length

        theta = math.radians(angle)
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        one_minus_cos = 1 - cos_theta

        # Rodrigues' 회전
        new_x = (cos_theta + x * x * one_minus_cos) * vx + (x * y * one_minus_cos - z * sin_theta) * vy + (x * z * one_minus_cos + y * sin_theta) * vz
        new_y = (y * x * one_minus_cos + z * sin_theta) * vx + (cos_theta + y * y * one_minus_cos) * vy + (y * z * one_minus_cos - x * sin_theta) * vz
        new_z = (z * x * one_minus_cos - y * sin_theta) * vx + (z * y * one_minus_cos + x * sin_theta) * vy + (cos_theta + z * z * one_minus_cos) * vz

        parts[1] = str(new_x)
        parts[2] = str(new_y)
        parts[3] = str(new_z)
        return ','.join(parts)

    def mirror(self, mirror_x=0, mirror_y=0, mirror_z=0) -> list:
        """
        CSV오브젝트 Mirror
        :param mirror_x: X축 대칭 여부 (1이면 반전)
        :param mirror_y: Y축 대칭 여부 (1이면 반전)
        :param mirror_z: Z축 대칭 여부 (1이면 반전)
        :return: 변환된 줄 리스트
        """
        sx = -1 if mirror_x else 1
        sy = -1 if mirror_y else 1
        sz = -1 if mirror_z else 1

        # scale 함수 재활용
        return self.scale(sx, sy, sz)

