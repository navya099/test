# main.py
import logging
import math
from core.component.branch_condition import BranchCondition
from core.system.interactive_selector import InteractiveSelectorSystem
from core.world.world import World
from core.constants import EntityKey, ComponentKey
from alignment.rail import Rail
from alignment.alignment import Alignment
from vector3 import Vector3

# 시스템 임포트
from core.system.extract_start_info import ExtractStartInfoSystem
from core.system.get_target_track import GetTargetTrackSystem
from core.system.create_turnout_spec import CreateTurnoutSpecSystem

# 설정 임포트
from config import (
    BRANCH_START_STATION, BRANCH_END_STATION, BRANCH_TARGET_TRACK,
    TRACK_OFFSET_X, MAIN_TRACK_NAME
)

logger = logging.getLogger(__name__)


class Main:
    def __init__(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    def main(self):
        logger.info("1. 로컬 좌표 기반 선형 생성")

        # 1. 자선(Mainline) 로컬 좌표 생성
        # (실무에서는 외부 API나 입력값을 받겠지만, 여기서는 100m 직선을 25m 간격으로 생성)
        main_alignment = self._create_local_mainline(
            length=BRANCH_END_STATION - BRANCH_START_STATION,  # 100m
            interval=25.0,
            start_station=BRANCH_START_STATION
        )

        # 2. 타선(Target Track) 생성
        # 타선 파일 대신, "7m 횡거리에 위치한 평행선"을 로컬 좌표로 즉시 생성
        target_alignment = self._create_local_target_track(
            length=BRANCH_END_STATION - BRANCH_START_STATION,
            interval=25.0,
            start_station=BRANCH_START_STATION,
            offset_x=TRACK_OFFSET_X,  # 7m
            railindex=BRANCH_TARGET_TRACK
        )

        tracks = [main_alignment, target_alignment]

        logger.info("2. ECS 파이프라인 실행")
        world = World()
        world.add_entity(EntityKey.MAIN_ALIGNMENT, main_alignment)
        world.add_entity(EntityKey.TRACKS, tracks)

        condition = BranchCondition(
            start_station=BRANCH_START_STATION,
            end_station=BRANCH_END_STATION,
            target_track=BRANCH_TARGET_TRACK
        )
        world.add_component(ComponentKey.BRANCH_CONDITION, condition)

        world.add_system(ExtractStartInfoSystem())
        world.add_system(GetTargetTrackSystem())
        world.add_system(CreateTurnoutSpecSystem())
        # 2. 사용자 선택
        world.add_system(InteractiveSelectorSystem())

        world.run()

        # 3. 결과 출력
        spec = world.components[ComponentKey.TURNOUT_SPEC]
        result_msg = (
            f"\n=== 건넘선 설계 결과 ===\n"
            f"곡선장(cl): {spec.start_length} m\n"
            f"직선장(sl): {spec.middle_length} m\n"
            f"반지름(R): {spec.radius:.2f} m\n"
            f"접선각(θ): {math.degrees(spec.cross_angle):.2f}°\n"
            f"========================="
        )
        logger.info(result_msg)
        print(result_msg)  # GUI 제거했으므로 콘솔 출력

    def _create_local_mainline(self, length: float, interval: float, start_station: int) -> Alignment:
        """로컬 좌표계의 자선 생성 (X축 방향으로 직선)"""
        al = Alignment(MAIN_TRACK_NAME)
        num_points = int(length / interval) + 1
        for i in range(num_points):
            station = start_station + i * interval
            rail = Rail(station=station, railindex=0, rail_x=0.0, rail_y=0.0, object_index=0)
            # X축 방향으로 진행 (station에 비례하여 X좌표 증가)
            rail.coord = Vector3(x=(i * interval), y=0.0, z=float(station))
            al.raildata.append(rail)

        al.compute_directions_for_alignment()
        return al

    def _create_local_target_track(self, length: float, interval: float, start_station: int, offset_x: float,
                                   railindex: int) -> Alignment:
        """로컬 좌표계의 타선 생성 (자선에서 Y축으로 offset만큼 떨어진 평행선)"""
        al = Alignment(f"타선_{railindex}")
        num_points = int(length / interval) + 1
        for i in range(num_points):
            station = start_station + i * interval
            # rail_x에는 오프셋을, rail_y에는 0을 넣음
            rail = Rail(station=station, railindex=railindex, rail_x=offset_x, rail_y=0.0, object_index=0)
            # 타선의 좌표는 (X, offset_x, Z)
            rail.coord = Vector3(x=(i * interval), y=offset_x, z=float(station))
            al.raildata.append(rail)

        al.compute_directions_for_alignment()
        return al


if __name__ == '__main__':
    Main().main()