
class BracketFittngResolver:
    @staticmethod
    def resolve(fit, idxlib):
        name = fit.label.replace(".csv", "")
        fit.index = idxlib.get_index(name)
