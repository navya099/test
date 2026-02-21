import tkinter as tk

from gui.viewmodel.bracket_input import BracketViewModel
from model.bracket import Bracket


class TKBracketAdapter:
    """TKBRACKET객체 어댑터"""
    @staticmethod
    def from_vm(b: BracketViewModel, rail_index) -> Bracket:
        """뷰 모델로부터 도메인 객체 생성"""
        return Bracket(
            rail_no=rail_index,
            type=b.bracket_type.get(),
            xoffset=b.xoffset.get(),
            yoffset=b.yoffset.get(),
            rotation=b.rotation.get(),
            rail_type=b.rail_type.get(),
            index=-1,
        )

    @staticmethod
    def from_dto(data: Bracket) -> BracketViewModel:
        """역변환 도메인으로부터 뷰 모델 생성"""
        return BracketViewModel(
            rail_no=tk.IntVar(value=data.rail_no),
            xoffset=tk.DoubleVar(value=data.xoffset),
            yoffset=tk.DoubleVar(value=data.yoffset),
            rotation=tk.DoubleVar(value=data.rotation),
            rail_type=tk.StringVar(value=data.rail_type),
            bracket_type=tk.StringVar(value=data.type),
        )