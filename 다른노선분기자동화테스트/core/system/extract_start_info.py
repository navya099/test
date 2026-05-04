from core.system.system import System
import logging

class ExtractStartInfoSystem(System):
    """자선에서 시작 정보를 추출"""
    def execute(self, entities, components):
        start_angle = None
        start_point = None
        main_al = entities['main_alignment']
        condition = components['branch_condition']
        for rail in main_al.raildata:
            if rail.station == condition.start_station:
                start_angle = rail.direction.toradian()
                start_point = rail.coord
                components['start_angle'] = start_angle
                components['start_point'] = start_point
                logging.info(f"[ExtractStartInfoSystem] start_angle={start_angle}, start_point={start_point}")

                break



