from dataclasses import dataclass

from Electric.Overhead.Pole.poletype import PoleType
from Electric.Overhead.Structure.beamtype import BeamType
from model.beam import Beam
from model.bracket import Bracket
from model.colum import Column


@dataclass
class BeamAssembly:
    """빔 구성요소
    Attributes:
        beam:빔 객체
        columns: 기둥들
        brackets:브래킷들
    """
    beam: Beam
    columns: list[Column]
    brackets: list[Bracket]

    @classmethod
    def create_from_install(cls, install, idxlib):
        """팩토리메서드"""
        beam = cls._create_beam(install, idxlib)
        columns = cls._create_columns(install, idxlib)
        brackets = cls._create_brackets(install, idxlib)

        return cls(beam, columns, brackets)

    @staticmethod
    def _create_beam(install, idxlib):
        length = abs(install.left_x) + abs(install.right_x)
        if install.beam_type == BeamType.PIPE:
            b_name = '깅관빔'
        elif install.beam_type == BeamType.TRUSS:
            b_name = '트러스빔'
        elif install.beam_type == BeamType.TRUSS_RHAMEN:
            b_name = '트러스라멘빔'
        else:
            b_name = '트러스빔'
        name = f"{b_name}-{int(length)}m"
        index = idxlib.get_index(name)

        return Beam(
            type=install.beam_type,
            length=length,
            index=index
        )

    @staticmethod
    def _create_columns(install, idxlib):
        columns = []
        xs = [install.left_x, install.right_x]
        if install.pole_type == PoleType.PIPE.label:
            pole_type = PoleType.PIPE.label
        elif install.pole_type == PoleType.H_BEAM.label:
            pole_type = PoleType.H_BEAM.label
        elif install.pole_type == PoleType.STEEL.label:
            pole_type = PoleType.STEEL.label
        else:
            pole_type = PoleType.PIPE.label
        for x in xs[:install.pole_count]:
            name = f"{pole_type}-{install.pole_width}-{int(install.pole_height)}m"
            index = idxlib.get_index(name)

            columns.append(
                Column(
                    type=pole_type,
                    width=install.pole_width,
                    xoffset=x,
                    yoffset=0.0,
                    height=install.pole_height,
                    index=index
                )
            )
        return columns

    @staticmethod
    def _create_brackets(install, idxlib):
        brackets = []
        for rail_name_var, rail_idx_var, bracket_var, x_var, y_var, rotate_var in install.brackets:
            rail_name = rail_name_var.get()
            rail_idx = rail_idx_var.get()
            bracket = bracket_var.get()
            x = x_var.get()
            y = y_var.get()
            rot = rotate_var.get()
            bracket = bracket.replace('.csv', '')
            index = idxlib.get_index(bracket)

            brackets.append(
                Bracket(
                    rail_no=rail_name,
                    type=bracket,
                    xoffset=x,
                    yoffset=y,
                    rotation=rot,
                    index=index
                )
            )
        return brackets