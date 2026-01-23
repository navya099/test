from dataclasses import dataclass
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
        name = f"{install.beam_type}-{int(length)}m"
        index = idxlib.get_index(name)

        return Beam(
            type=install.beam_type,
            length=length,
            index=index,
            name=name,
            x=install.left_x,
            y=0,
            rotation=0,
        )

    @staticmethod
    def _create_columns(install, idxlib):
        columns = []
        xs = [install.left_x, install.right_x]
        for x in xs[:install.pole_count]:
            name = f"{install.pole_type}-{install.pole_width}-{int(install.pole_height)}m"
            index = idxlib.get_index(name)

            columns.append(
                Column(
                    name=name,
                    type=install.pole_type,
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

        for rail in install.brackets:  # RailData 단위로 순회
            for b in rail.brackets:  # 이미 Bracket 객체임
                name = b.type
                name = name.replace('.csv', '')
                index = idxlib.get_index(name)

                brackets.append(
                    Bracket(
                        rail_no=rail.index,
                        type=name,
                        xoffset=b.xoffset,
                        yoffset=b.yoffset,
                        rotation=b.rotation,
                        index=index,
                        rail_type=''
                    )
                )

        return brackets
