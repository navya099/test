from core.system.system import System
from core.constants import EntityKey, ComponentKey


class ExtractStartInfoSystem(System):
    requires_entities = frozenset({EntityKey.MAIN_ALIGNMENT})
    requires_components = frozenset({ComponentKey.BRANCH_CONDITION})
    produces_components = frozenset({ComponentKey.START_INFO})

    def execute(self, entities, components):
        main_al = entities[EntityKey.MAIN_ALIGNMENT]
        condition = components[ComponentKey.BRANCH_CONDITION]

        for rail in main_al.raildata:
            if abs(rail.station - condition.start_station) < 1e-3:
                components[ComponentKey.START_INFO] = {
                    "angle": rail.direction.toradian(),
                    "point": rail.coord
                }
                self.logger.info(f"시작점 추출 완료: station={rail.station}")
                return
        raise ValueError(f"start_station={condition.start_station}에 해당하는 rail을 찾을 수 없습니다.")