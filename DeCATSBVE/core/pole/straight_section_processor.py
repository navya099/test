from core.bracket.helper_bracket_create import BracketCreator
from core.bracket.steady_arm_helper import SteadyArmHelper


class StraightSectionProcessor:
    @staticmethod
    def process(pole, dataprocessor, idxlib, rotation, stagger_flip=False):
        _, cw_height = dataprocessor.get_contact_wire_and_massanger_wire_info(pole.structure)
        # stagger 방향 결정
        if stagger_flip:
            stagger = 0.2 if pole.base_type == 'I' else -0.2
        else:
            stagger = -0.2 if pole.base_type == 'I' else 0.2

        # bracket 생성 (flip은 bracket 뒤집기만 담당)
        bracket = BracketCreator.create_bracket(
            pole, dataprocessor, idxlib, rotation, stagger
        )

        # steady arm fitting 추가
        fit = SteadyArmHelper.create_fitting(pole, dataprocessor, idxlib, stagger, cw_height, rotation)
        bracket.fittings.append(fit)
        pole.brackets.append(bracket)