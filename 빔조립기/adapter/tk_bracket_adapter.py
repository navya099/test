from model.bracket import Bracket


class TKBracketAdapter:
    @staticmethod
    def from_vm(b, rail_index) -> Bracket:
        return Bracket(
            rail_no=rail_index,
            type=b.bracket_type.get(),
            xoffset=b.xoffset.get(),
            yoffset=b.yoffset.get(),
            rotation=b.rotation.get(),
            rail_type=b.rail_type.get(),
            index=-1,
        )