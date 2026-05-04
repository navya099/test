import logging

from core.system.system import System
class CurveCalculatorSystem(System):
    """곡선 제원 계산"""
    def execute(self, entities, components):
        condition = components['branch_condition']
        s = components['turnout_spec'].cross_angle
        l = components['turnout_spec'].middle_length
        r = l / s
        logging.info(f'[CurveCalculatorSystem]: find r = {r}')

