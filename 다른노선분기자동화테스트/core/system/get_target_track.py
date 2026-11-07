# core/system_impl/get_target_track.py
from core.system.system import System
from core.constants import EntityKey, ComponentKey

class GetTargetTrackSystem(System):
    requires_entities = frozenset({EntityKey.TRACKS})
    requires_components = frozenset({ComponentKey.BRANCH_CONDITION})
    produces_entities = frozenset({EntityKey.TARGET_TRACK})

    def execute(self, entities, components):
        condition = components[ComponentKey.BRANCH_CONDITION]
        tracks = entities[EntityKey.TRACKS]

        for track in tracks:
            if track.raildata and track.raildata[0].railindex == condition.target_track:
                entities[EntityKey.TARGET_TRACK] = track
                self.logger.info(f"타겟 트랙 발견: {track.name} (idx={condition.target_track})")
                return
        raise ValueError(f"target_track={condition.target_track}에 해당하는 트랙이 없습니다.")