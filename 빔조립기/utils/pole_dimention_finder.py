class PoleDimensionFinder:
    @staticmethod
    def find_pole_dimension(pole):
        pipepole_dimension_tables = {
            'P10': 0.2674,
            'P12': 0.3285,
            'P14': 0.3556,
            'P16': 0.4064,
            'P18': 0.4572,
            'P20': 0.5
        }
        hbeam_pole_dimension_tables = {
        'H250x250': 0.25,
            'H300x300': 0.3
        }
        steel_pole_dimension_tables = {
            'L75x300x400': 0.3,
            'L75x450x450': 0.45,
            'L90x450x450': 0.45
        }

        # 타입별 딕셔너리 매핑
        pole_dimension_tables = {
            'PIPE': pipepole_dimension_tables,
            'H_BEAM': hbeam_pole_dimension_tables,
            'STEEL': steel_pole_dimension_tables
        }

        # pole.type에 따라 해당 딕셔너리에서 width 키를 찾아 반환
        return pole_dimension_tables[pole.type.name][pole.width]