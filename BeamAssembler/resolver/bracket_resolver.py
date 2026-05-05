from controller.library_controller import IndexLibrary
from model.bracket import Bracket
from resolver.fitting_resolver import BracketFittngResolver


class BracketResolver:
    @staticmethod
    def resolve(brackets: list[Bracket], idxlib: IndexLibrary):
        for b in brackets:
            name = b.type.replace(".csv", "")
            b.type = name
            b.index = idxlib.get_index(name)
            for f in b.fittings:
                BracketFittngResolver.resolve(f, idxlib)