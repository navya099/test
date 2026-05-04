from core.system.system import System
import logging

class GetTargetTrackSystem(System):
    """타겟 트랙 인덱스로부터 타겟 트랙 얻기"""
    def execute(self, entities, components):
        condition = components['branch_condition']
        target_idx = condition.target_track
        tracks = entities['tracks']

        for track in tracks:
            if track.raildata[0].railindex == target_idx:
                entities['target_track'] = track
                logging.info(f'[GetTargetTrackSystem]: target_idx={target_idx}')
                break
