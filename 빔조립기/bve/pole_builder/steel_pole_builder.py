from bve.pole_builder.base_pole_builder import BasePoleBuilder
from utils.pole_dimention_finder import PoleDimensionFinder


class SteelPoleBuilder(BasePoleBuilder):
    def build(self):
        self._build_header()
        self.build_body()
        dimension_str = PoleDimensionFinder.get_pole_type_by_dimension('STEEL', self.diameter)
        self.save_text(f'c:/temp/조립철주_{dimension_str}_{self.length}m.csv')
        return self.path

    def build_body(self):
        if self.diameter == 0.4:
            fname = '조립철주_L75X300X400'
        else:
            fname = '조립철주_L90X450X450'
        with open(f'c:/temp/{fname}.csv', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith("AddVertex"):
                parts = line.split(",")

                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                if y == 8.4:
                    y = self.length - 0.6
                if y == 8.6:
                    y = self.length - 0.6 + 0.2
                parts[1] = f" {round(x, 3)}"
                parts[2] = f" {round(y, 3)}"
                parts[3] = f" {round(z, 3)}"

                self.text.append(",".join(parts))
            else:
                self.text.append(line)
