from curvepost.base_builder import CurveDATABuilder
from model.curve.ipdata import IPdata


class CIVIL3DCURVEDATABuilder(CurveDATABuilder):
    def build(self, data, brokenchain) -> list[IPdata]:
        raise NotImplementedError

    def preprocess(self, data, brokenchain) -> IPdata:
        raise NotImplementedError
