from core.bracket.helper_bracket_create import BracketCreator

class StraightSectionProcessor:
    @staticmethod
    def process(pole, dataprocessor, idxlib, current_curve, rotation, stagger_flip=False):
        # stagger 방향 결정
        if stagger_flip:
            stagger = 0.2 if pole.base_type == 'I' else -0.2
        else:
            stagger = -0.2 if pole.base_type == 'I' else 0.2

        # bracket 생성 (flip은 bracket 뒤집기만 담당)
        bracket = BracketCreator.create_bracket(
            pole, dataprocessor, idxlib, current_curve, rotation, stagger
        )
        pole.brackets.append(bracket)