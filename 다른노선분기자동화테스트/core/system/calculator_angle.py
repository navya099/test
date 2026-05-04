import math
from core.system.system import System
import logging

class CalculateAngleSystem(System):
    """자선분기 조건으로부터 곡선 각도 계산"""
    def execute(self, entities, components):
        condition = components['branch_condition']
        length = condition.length

        # 시작 각도
        start_angle = components['start_angle']
        # 직선 길이
        straight_length = components['turnout_spec'].middle_length

        # 대상 선로의 끝 측점에서의 x값
        target_track = entities['target_track']
        start_station = condition.start_station
        x = 0.0
        for rail in target_track.raildata:
            if rail.station == start_station:
                x = rail.rail_x
                break

        # 각도 계산 (의도에 따라 Δy, Δx로 조정 필요)
        angle = math.atan2(x, straight_length)

        # 결과 저장
        components['turnout_spec'].cross_angle = angle
        logging.info(f'[CalculateAngleSystem]: angle = {angle}')