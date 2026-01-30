from dataclasses import dataclass

from model.objmodel.csvobject import CSVObject


@dataclass
class PreviewObject:
    """
    Attributes:
        csvobj: 실제 모델
        track_name: 선로명
        pivot: 배치점
        color: 색상
        category: 카테고리
    """
    csvobj: CSVObject       # 실제 모델
    track_name: str         # item의 트랙 이름
    pivot: tuple            # WORLD 좌표 기준 pivot
    color: str = "black"    # 옵션: track_name 기반 색상
    category: str = ''
