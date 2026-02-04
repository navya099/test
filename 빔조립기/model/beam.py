from dataclasses import dataclass

from Electric.Overhead.Structure.beamtype import BeamType


@dataclass
class Beam:
    """빔 구성요소
    Attributes:
        name: 빔 표시 이름
        type: 빔 종류
        length: 빔 길이
        index: 빔 오브젝트 인덱스
        start_pole: 빔 시작 전주
        end_pole: 빔 끝 전주
        x: 설치 offset
        y: 설치 offset
        rotation: 회전각(ㅇ)
        """

    type: BeamType
    name: str | None = None
    length: float | None = None
    index: int | None = None
    start_pole: int | None = None
    end_pole: int | None = None
    x: float | None = None
    y: float | None = None
    rotation: float | None = None