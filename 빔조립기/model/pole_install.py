from dataclasses import dataclass, field

from Electric.Overhead.Pole.poletype import PoleType
from Electric.Overhead.Structure.beamtype import BeamType
from model.beam_assembly import BeamAssembly


@dataclass
class PoleInstall:
    """최상위: 설치 단위
        Attributes:
            station:측점
            pole_number:전주번호
            rail_count:전주가 감싸는 선로갯수
            left_x:좌측 건식게이지
            right_x:우측 건식게이지

            beam_type: BeamType
            pole_type: PoleType
            pole_width: str
            pole_height: float
            pole_count: int

            rails: 선로객체들
            beam_assembly: 빔
    """
    station: float = 0.0
    pole_number: str = ''
    left_x: float = 0.0
    right_x: float = 0.0
    rail_count: int = 0

    beam_type:  BeamType = BeamType.H_BEAM
    pole_type: PoleType = PoleType.PIPE
    pole_width: str = ''
    pole_height: float = 0.0
    pole_count: int = 0

    beam_assembly: BeamAssembly | None = None

    rails: list | None = None

    def to_bve(self):
        """BVE 구문화 메서드"""
        text = ''
        text += f',;{self.pole_number}\n'
        text += f'{self.station}\n'
        text += ',;급전선지지설비\n'
        text += '.freeobj 0;1119;0;,;전주대용물1선\n'
        text += '.freeobj 1;1119;0;,;전주대용물1선\n'
        text += ',;기둥\n'
        for c in self.beam_assembly.columns:
            text += f'.freeobj 0;{c.index};{c.xoffset};0;0;,;{c.type}\n'
        text += ',;빔\n'
        text += f'.freeobj 0;{self.beam_assembly.beam.index};{self.beam_assembly.columns[0].xoffset};0;0;,;{self.beam_assembly.beam.type}\n'

        text += ',;브래킷\n'

        for rail in self.rails:
            brackets = rail.brackets
            n = len(brackets)
            s = 1
            offs = self.offsets(n, s)

            for i, br in enumerate(brackets):
                offset = offs[i]
                station = self.station + offset

                text += f'{station}\n'
                text += f',;{br.rail_type}\n'
                text += (
                    f'.freeobj {br.rail_no};{br.index};'
                    f'{br.xoffset};{br.yoffset};{br.rotation};,;{br.type}\n'
                )
        return text

    @staticmethod
    def offsets(n, s):
        if n == 1:
            return [0.0]
        if n == 2:
            return [-s * 0.5, s * 0.5]
        # n >= 3
        return [(i - (n - 1) / 2) * s * 0.5 for i in range(n)]

    def _flatten_brackets(self):
        return [b for rail in self.rails for b in rail.brackets]