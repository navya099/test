from common.generatorfactory import GeneratorFactory

class MainRunner:
    def __init__(self, state, logger, generator_type):
        self.state = state
        self.log = logger
        self.generator_type = generator_type

    def run(self):
        generator = GeneratorFactory.create(
            self.generator_type,
            state=self.state,
            logger=self.log
        )
        generator.generate()


