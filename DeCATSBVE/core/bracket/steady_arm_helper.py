from core.bracket.fitting_data import FittingDATA


class SteadyArmHelper:
    @staticmethod
    def get_index(dataprocessor, base_type):
        steady_arm_dict = dataprocessor.get_steady_arm_fittings()

        return steady_arm_dict[base_type][0] if base_type == 'I' else steady_arm_dict[base_type][1]

    @staticmethod
    def create_fitting(pole, dataprocessor, idxlib, stagger, cw_height, rotation):
        steady_arm_index = SteadyArmHelper.get_index(dataprocessor, pole.base_type)
        steady_arm_name = idxlib.get_name(steady_arm_index)

        return FittingDATA(
            index=steady_arm_index,
            offset=(stagger, cw_height),
            rotation=rotation,
            label=steady_arm_name
        )