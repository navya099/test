from curvepost.curvegenerator import CurveGenerator
from gradepost.gradegenerator import GradeGenerator
from kmpost.kmgenerator import KMGenerator
from structurepost.structuregenerator import StructureGenerator


class GeneratorFactory:
    GENERATORS = {
        "거리표": KMGenerator,
        "곡선표": CurveGenerator,
        "기울기표": GradeGenerator,
        "구조물표": StructureGenerator,
    }

    @staticmethod
    def create(generator_type, state, logger):
        if generator_type not in GeneratorFactory.GENERATORS:
            raise ValueError(f"알 수 없는 생성기 타입: {generator_type}")

        return GeneratorFactory.GENERATORS[generator_type](state, logger)
