from bve.beam_builder.base_builder import BaseBeamBuilder

class PIPEBeamBuilder(BaseBeamBuilder):
    def __init__(self, length):
        super().__init__(length)
    def build(self):
        raise NotImplementedError()
