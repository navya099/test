from controller.library_controller import IndexLibrary
from model.bracket import Bracket


class BracketResolver:
    @staticmethod
    def resolve(brackets: list[Bracket], idxlib: IndexLibrary):
        for b in brackets:
            name = b.type.replace(".csv", "")
            b.type = name
            b.index = idxlib.get_index(name)