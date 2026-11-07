# core/system_impl/generate_branch_coords.py
import math
from core.system.system import System
from core.constants import EntityKey, ComponentKey
from math_utils import generate_arc_points, generate_straight_points


class GenerateBranchCoordsSystem(System):
    """설계 제원을 바탕으로 실제 분기 경로 좌표(Polyline)를 생성한다."""
    requires_entities = frozenset({EntityKey.TARGET_TRACK})
    requires_components = frozenset({ComponentKey.START_INFO, ComponentKey.TURNOUT_SPEC})
    produces_components = frozenset({ComponentKey.BRANCH_COORDS})

    def execute(self, entities, components):
        start_info = components[ComponentKey.START_INFO]
        spec = components[ComponentKey.TURNOUT_SPEC]

        # 시작점 정보
        start_point = (start_info["point"].x, start_info["point"].y)
        start_angle = start_info["angle"]  # 라디안

        # 설계 제원
        cl = spec.start_length
        sl = spec.middle_length
        R = spec.radius
        theta = spec.cross_angle

        # 곡선의 방향 결정 (타겟 트랙이 자선의 왼쪽(+Y)인지 오른쪽(-Y)인지)
        target_track = entities[EntityKey.TARGET_TRACK]
        # 시작점에서 타겟 트랙의 rail_x 부호를 확인하여 좌/우 판별
        rail_x = self._get_target_rail_x(target_track, start_info["point"].z)
        # 로컬 좌표계 기준, rail_x > 0 이면 왼쪽(반시계, +1), < 0 이면 오른쪽(시계, -1)
        direction_sign = 1 if rail_x > 0 else -1

        all_points = []

        # 1. 곡선 1 (cl, R, +theta)
        arc1_points = generate_arc_points(
            start_point, start_angle, R, theta, direction_sign, num_points=20
        )
        all_points.extend(arc1_points)

        # 곡선 1의 끝점과 끝 각도
        end_point1 = arc1_points[-1]
        end_angle1 = start_angle + direction_sign * theta

        # 2. 직선 (sl)
        if sl > 0:
            straight_points = generate_straight_points(
                end_point1, end_angle1, sl, num_points=2
            )
            # 중복점 제거 (곡선 끝점과 직선 시작점)
            all_points.extend(straight_points[1:])
            end_point2 = straight_points[-1]
        else:
            end_point2 = end_point1

        # 3. 곡선 2 (cl, R, -theta)
        # 직선 구간에서 각도 유지, 반대 방향 회전
        arc2_points = generate_arc_points(
            end_point2, end_angle1, R, theta, -direction_sign, num_points=20
        )
        all_points.extend(arc2_points[1:])  # 중복점 제거

        # 4. 최종 결과 저장
        components[ComponentKey.BRANCH_COORDS] = {
            "points": all_points,
            "start_point": start_point,
            "end_point": all_points[-1],
            "end_angle": start_angle  # S자 형상이므로 최종 각도는 시작 각도와 동일(평행)
        }

        self.logger.info(f"분기 경로 좌표 생성 완료: {len(all_points)}개 포인트")

    def _get_target_rail_x(self, target_track, station):
        for rail in target_track.raildata:
            if abs(rail.station - station) < 1e-3:
                return rail.rail_x
        return 0.0