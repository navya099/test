from core.bracket.fitting_data import FittingDATA
from core.bracket.helper_bracket_create import BracketCreator
from core.bracket.steady_arm_helper import SteadyArmHelper
from utils.math_util import calculate_curve_stagger

class CurveSectionProcessor:
    @staticmethod
    def process(pole, dataprocessor, idxlib, current_curve, rotation, flip=False):
        _, cw_height = dataprocessor.get_contact_wire_and_massanger_wire_info(pole.structure)
        direction = 1 if pole.radius > 0 else -1
        default_stagger = -0.2 * direction
        stagger = calculate_curve_stagger(pole.cant, contact_wire_height=cw_height,
                                          offset=default_stagger, direction=direction)

        bracket = BracketCreator.create_bracket(pole, dataprocessor, idxlib, current_curve, rotation, stagger, flip)

        # steady arm fitting 추가
        fit = SteadyArmHelper.create_fitting(pole, dataprocessor, idxlib, stagger, cw_height, rotation, flip)

        bracket.fittings.append(fit)
        pole.brackets.append(bracket)