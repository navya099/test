from dataclasses import dataclass, field

@dataclass
class PoleInstall:
    """최상위: 설치 단위
        Attributes:
            station:측점
            pole_number:전주번호
            rail_count:전주가 감싸는 선로갯수
            pole_count: 전주 갯수
            beam_count: 빔 갯수

            poles: 전주들
            beams: 빔 객체들
            rails: 선로객체들
            equips: 장비들
    """
    station: float = 0.0
    pole_number: str = ''
    rail_count: int = 0
    pole_count: int = 0
    beam_count: int = 0
    beams: list | None = None
    poles: list | None = None
    rails: list | None = None
    equips: list | None = None