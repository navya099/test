from bve.pole_builder.base_pole_builder import BasePoleBuilder
from utils.pole_dimention_finder import PoleDimensionFinder


class HBEAMBuiilder(BasePoleBuilder):
    def __init__(self, length, diameter):
        super().__init__(length, diameter)
    def build(self):
        self.build_body()
        dimension_str = PoleDimensionFinder.get_pole_type_by_dimension('H_BEAM', self.diameter)
        self.save_text(f'c:/temp/H형주_{dimension_str}_{self.length}m.csv')
        return self.path
    def build_body(self):
        fname = 'H빔250' if self.diameter == 0.25 else 'H빔350'
        with open(f'c:/temp/{fname}.csv', 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith("AddVertex"):
                parts = line.split(",")

                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                if y == 8.664:
                    y = self.length - 0.336

                parts[1] = f" {round(x, 3)}"
                parts[2] = f" {round(y, 3)}"
                parts[3] = f" {round(z, 3)}"

                self.text.append(",".join(parts))
            else:
                self.text.append(line)
