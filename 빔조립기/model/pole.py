from dataclasses import dataclass

from Electric.Overhead.Pole.poletype import PoleType
from model.rail import RailData


@dataclass
class Pole:
    """전주 객체
    Attributes:
        type: 전주타입
        uid: 전주 uid
        display_name: UI 표시 전주 이름
        length: 전주길이(m)
        width: 전주 치수(mm)
        index: BVE 오브젝트 인덱스
        base_rail_index: 기준 레일 인덱스
        base_rail_uid: 기준 레일 uid(참조용)
        xoffset: 기준레일로부터 오프셋
    """
    type: PoleType
    uid: str
    display_name: str | None = None
    length: float | None = None
    width: float | None = None
    index: int | None = None
    base_rail_index: int | None = None
    base_rail_uid: str | None = None
    # 배치 정보
    xoffset: float | None = None
    iscustom: bool | None = None
