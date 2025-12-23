from dataclasses import dataclass, field

from Electric.Overhead.Pole.poletype import PoleType
from Electric.Overhead.Structure.beamtype import BeamType
from library import LibraryManager
import re
import pandas as pd
from typing import TypeVar, Callable

# 전역변수
SHEET_ID = "1z0aUcuZCxOQp2St3icbQMbOkrSPfJK_8iZ2JKFDbW8c"
SHEET_NAME = "freeobj"  # ← 원하는 시트 이름
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
T = TypeVar("T")


class IndexLibrary:
    def __init__(self, df):
        self.df = df

    def get_index(self, filename):
        row = self.df[self.df["파일명"] == filename]
        if row.empty:
            return None
        return int(row.iloc[0]["인덱스"])

    def get_path(self, filename):
        row = self.df[self.df["파일명"] == filename]
        if row.empty:
            return None
        return row.iloc[0]["경로"]

    def search(self, keyword):
        return self.df[self.df["파일명"].str.contains(keyword, na=False)]


def input_default(prompt: str, default: T, cast: Callable[[str], T]) -> T:
    user = input(f"{prompt} [{default}]: ")
    if user.strip() == "":
        return default
    return cast(user)


class Inputdata:
    """입력 데이터 클래스"""

    def input_values(self):
        # 시작
        self.station = input_default('0: 측점 입력', 87943.0, cast=float)
        self.pole_number = input_default('1: 전주번호', '47-27', str)
        self.railtype = input_default('2: 선로타입 입력', '준고속철도', str)
        self.left_x_offset = input_default('3: 최외곽 좌측 선로 x offset 입력', -12.0, cast=float)
        self.right_x_offset = input_default('4: 최외곽 우측 선로 x offset 입력', 9.0, cast=float)
        self.beam_type = input_default('5: 빔 종류 입력', 'TRUSS', cast=str)
        self.pole_type = input_default('6: 전주 종류 입력', 'PIPE', cast=str)
        self.pole_width = input_default('7: 전주 직경 입력', 'P10', cast=str)
        self.pole_height = input_default('8: 전주 높이 입력', 9.0, cast=float)


@dataclass
class Feederdata:
    """급전선데이터
    Attributes:
        type: 급전선 지지물 종류
        index: 급전선 지지물 인덱스
        xoffset: 선로중심 기준 x 오프셋
        yoffset: 선로중심 기준 y 오프셋
        """
    type: str = ''
    index: int = 0
    xoffset: float = 0.0
    yoffset: float = 0.0


@dataclass
class Bracket:
    """가동브래킷
    Attributes:
        rail_no:선로번호
        type: 브래킷 종류
        xoffset: x위치
        yoffset: y위치
        rotation: 회전
        index: 브래킷 오브젝트 인덱스
        """
    rail_no: int
    type: str
    xoffset: float
    yoffset: float
    rotation: float
    index: int


@dataclass
class Column:
    """전주 기둥
        Attributes:
            type: 기둥 종류
            width: 기둥 폭
            xoffset: x위치
            yoffset: y위치
            index: 기둥 오브젝트 인덱스
            """
    type: PoleType
    width: float
    xoffset: float
    yoffset: float
    height: float
    index: int


@dataclass
class Beam:
    """빔 구성요소
    Attributes:
        type: 빔 종류
        length: 빔 길이
        index: 빔 오브젝트 인덱스
        """
    type: BeamType
    length: float
    index: int


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
        if install.pole_type == PoleType.PIPE:
            pole_type = '강관주'
        else:
            pole_type = 'H형주'
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
        for i in range(install.rail_count):
            x = 0
            name = "CaKo250-OpG3.5-I"
            index = idxlib.get_index(name)

            brackets.append(
                Bracket(
                    rail_no=i + 1,
                    type=name,
                    xoffset=x,
                    yoffset=0.0,
                    rotation=0,
                    index=index
                )
            )
        return brackets


@dataclass
class PoleInstall:
    """최상위: 설치 단위
        Attributes:
            station:측점
            pole_number:전주번호
            railtype:선로종류(일반철도,준고속철도,고속철도)
            rail_count:전주가 감싸는 선로갯수
            left_x:기준 선로로부터 최외곽 -X OFFSET
            right_x:기준 선로로부터 최외곽 X OFFSET
            gauge:건식게이지

            beam_type: BeamType
            pole_type: PoleType
            pole_width: str
            pole_height: float
            pole_count: int

            beam: 빔
    """
    station: float = 0.0
    pole_number: str = ''
    railtype: str = ''
    rail_count: int = 0
    left_x: float = 0.0
    right_x: float = 0.0
    gauge: float = 0.0

    beam_type: BeamType | None = None
    pole_type: PoleType | None = None
    pole_width: str = ''
    pole_height: float = 0.0
    pole_count: int = 0

    beam: BeamAssembly | None = None

    def to_bve(self):
        """BVE 구문화 메서드"""
        text = ''
        text = f',;{self.pole_number}\n'
        text += f'{self.station}\n'
        text += ',;급전선지지설비\n'
        text += '.freeobj 0;1119;0;,;전주대용물1선\n'
        text += '.freeobj 1;1119;0;,;전주대용물1선\n'
        text += ',;기둥\n'
        for c in self.beam.columns:
            text += f'.freeobj 0;{c.index};{c.xoffset};0;0;,;{c.type}\n'
        text += ',;빔\n'
        text += f'.freeobj 0;{self.beam.beam.index};{self.beam.columns[0].xoffset};0;0;,;{self.beam.beam.type}\n'
        return text


def main():
    df = pd.read_csv(URL)

    # 라이브러리 준비
    lib = LibraryManager()
    lib.scan_library()
    idxlib = IndexLibrary(df)

    # 데이터 입력받기(추후GUI로 확장예정)
    inputdatas = Inputdata()
    inputdatas.input_values()

    # 설치 시작
    install = PoleInstall(
        station=inputdatas.station,
        pole_number=inputdatas.pole_number,
        railtype=inputdatas.railtype,
        rail_count=inputdatas.count_rail,
        left_x=inputdatas.left_x_offset,
        right_x=inputdatas.right_x_offset,
        gauge=inputdatas.gauge,
        beam_type=BeamType[inputdatas.beam_type],
        pole_type=PoleType[inputdatas.pole_type],
        pole_width=inputdatas.pole_width,
        pole_height=inputdatas.pole_height,
        pole_count=inputdatas.pole_count
    )
    # 어셈블리 로드
    install.beam = BeamAssembly.create_from_install(
        install, idxlib
    )

    print(install.to_bve())


if __name__ == '__main__':
    main()




