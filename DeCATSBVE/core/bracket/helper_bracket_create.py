from core.bracket.bracket_data import BracketDATA

class BracketCreator:
    @staticmethod
    def create_bracket(pole, dataprocessor, idxlib, rotation, stagger):
        i_type_index = dataprocessor.get_bracket_codes('일반개소', pole.structure, 'I')
        o_type_index = dataprocessor.get_bracket_codes('일반개소', pole.structure, 'O')
        bracket_index = i_type_index if pole.base_type == 'I' else o_type_index
        bracket_type = pole.base_type
        bracket_name = idxlib.get_name(bracket_index)
        bracket = BracketDATA(
            bracket_type=bracket_type,
            index=bracket_index,
            bracket_name=bracket_name,
            rotation=rotation
        )
        bracket.stagger = stagger
        return bracket