from core.bracket.helper_bracket_create import BracketCreator

class StraightSectionProcessor:
    @staticmethod
    def process(pole, dataprocessor, idxlib, current_curve, rotation, flip=False):
        stagger = -0.2 if pole.base_type == 'I' else 0.2
        bracket = BracketCreator.create_bracket(pole, dataprocessor, idxlib, current_curve, rotation, stagger, flip)
        pole.brackets.append(bracket)