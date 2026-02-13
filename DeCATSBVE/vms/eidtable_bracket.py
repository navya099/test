from core.bracket.bracket_data import BracketDATA


class BracketEditor:
    @staticmethod
    def update(pole ,dataprocseeor):
        """일반구간용"""
        current_type = pole.base_type
        current_curve = '직선' if pole.radius == 0 else '곡선'
        i, o  = dataprocseeor.get_bracket_type(pole.structure, current_curve)
        if current_type == 'I':
            index = i
        else:
            index = o
        bracket_name = current_type
        pole.brackets[0] = BracketDATA(bracket_type=current_type, index=index, bracket_name=bracket_name)