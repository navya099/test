class PoleDimensionFinder:
    @staticmethod
    def find_pole_dimension(pole):
        pole_dimension_tables = {
            'P10': 0.2674,
            'P12': 0.3285,
            'P14': 0.3556,
            'P16': 0.4064,
            'P18': 0.4572,
            'P20': 0.5
        }
        return pole_dimension_tables[pole.width]