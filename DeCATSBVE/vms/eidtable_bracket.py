from core.bracket.bracket_data import BracketDATA


class BracketEditor:
    @staticmethod
    def update(pole ,dataprocseeor, idxlib):
        """일반구간용"""
        current_type = pole.base_type
        i_type_index = dataprocseeor.get_bracket_codes('일반개소', pole.structure, 'I')
        o_type_index = dataprocseeor.get_bracket_codes('일반개소', pole.structure, 'O')
        if current_type == 'I':
            index = i_type_index
        else:
            index = o_type_index
        bracket_name = idxlib.get_name(index)
        pole.brackets[0] = BracketDATA(bracket_type=current_type, index=index, bracket_name=bracket_name)