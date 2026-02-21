from dataclasses import dataclass, field
import tkinter as tk

@dataclass
class TKInstallData:
    """최상위: TK설치 단위
    Attributes:
        station_var:측점
        pole_number_var:전주번호
        rail_count_var:전주가 감싸는 선로갯수
        pole_count_var: 전주 갯수
        beam_count_var: 빔 갯수

        poles_var: 전주들
        beams_var: 빔 객체들
        rails_var: 선로객체들
        equips_var: 장비들
        """
    iid: str
    isbeaminstall_var: tk.BooleanVar
    station_var: tk.DoubleVar
    pole_number_var: tk.StringVar
    rail_count_var: tk.IntVar
    pole_count_var: tk.IntVar
    beam_count_var: tk.IntVar
    beams_var: list | None = None
    poles_var: list | None = None
    rails_var: list | None = None
    equips_var: list | None = None