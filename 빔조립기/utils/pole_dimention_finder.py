class PoleDimensionFinder:
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
        'L75x300x400': 0.4,
        'L75x450x450': 0.45,
        'L90x450x450': 0.45
    }
    @staticmethod
    def find_pole_dimension(pole):
        # 타입별 딕셔너리 매핑
        pole_dimension_tables = {
            'PIPE': PoleDimensionFinder.pipepole_dimension_tables,
            'H_BEAM': PoleDimensionFinder.hbeam_pole_dimension_tables,
            'STEEL': PoleDimensionFinder.steel_pole_dimension_tables
        }

        # pole.type에 따라 해당 딕셔너리에서 width 키를 찾아 반환
        return pole_dimension_tables[pole.type.name][pole.width]

    @staticmethod
    def get_pole_type_by_dimension(pole_type, dimension):
        pole_dimension_tables = {
            'PIPE': PoleDimensionFinder.pipepole_dimension_tables,
            'H_BEAM': PoleDimensionFinder.hbeam_pole_dimension_tables,
            'STEEL': PoleDimensionFinder.steel_pole_dimension_tables
        }

        # 지정된 타입의 테이블에서만 검색
        table = pole_dimension_tables.get(pole_type)
        if not table:
            return None

        for width, dim in table.items():
            if dim == dimension:  # 정확히 일치하는 값만
                return width
        return None

