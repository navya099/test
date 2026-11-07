# core/system_impl/create_turnout_spec.py
import math
from core.system.system import System
from core.constants import EntityKey, ComponentKey
from core.component.cross_turnout_spec import CrossTurnoutSpecComponent
from config import CURVE_UNIT, STRAIGHT_UNIT, MIN_RADIUS


class CreateTurnoutSpecSystem(System):
    """곡선-직선-곡선 형상의 비선형 방정식을 수치 해석으로 푼다."""
    requires_entities = frozenset({EntityKey.TARGET_TRACK})
    requires_components = frozenset({ComponentKey.BRANCH_CONDITION})
    produces_components = frozenset({"turnout_candidates"})  # ★ 후보 리스트 생성2

    def execute(self, entities, components):
        condition = components[ComponentKey.BRANCH_CONDITION]
        target_track = entities[EntityKey.TARGET_TRACK]
        length = condition.length

        rail_x = self._get_target_rail_x(target_track, condition.start_station)
        if rail_x is None:
            raise ValueError(f"station={condition.start_station}에서 rail_x를 찾을 수 없습니다.")

        candidates = self._generate_candidates(length)
        if not candidates:
            raise ValueError(f"L={length}m에 대한 (cl, sl) 후보가 없습니다. CURVE_UNIT({CURVE_UNIT})을 확인하세요.")

        valid_solutions = []
        for cl, sl in candidates:
            theta = self._solve_theta(cl, sl, rail_x)
            if theta is None:
                continue
            R = cl / theta
            if R < MIN_RADIUS:
                continue  # 물리적 제약 탈락

            valid_solutions.append({
                "cl": cl, "sl": sl, "theta": theta, "R": R
            })

        if not valid_solutions:
            raise ValueError(f"L={length}, offset={rail_x}를 만족하는 유효한 분기기 제원이 없습니다.")

        # ★ 결과를 리스트로 저장
        components["turnout_candidates"] = valid_solutions
        self.logger.info(f"총 {len(valid_solutions)}개의 유효한 후보를 찾았습니다.")

    def _get_target_rail_x(self, target_track, start_station):
        for rail in target_track.raildata:
            if abs(rail.station - start_station) < 1e-3:
                return abs(rail.rail_x)
        return None

    def _generate_candidates(self, length):
        candidates = []
        max_cl = int(length // 2)
        for cl_int in range(int(CURVE_UNIT), max_cl + 1, int(CURVE_UNIT)):
            cl = float(cl_int)
            sl = length - 2 * cl
            if sl >= 0 and math.isclose(sl % STRAIGHT_UNIT, 0, abs_tol=1e-2):
                candidates.append((cl, sl))
        return candidates

    def _solve_theta(self, cl, sl, rail_x):
        """
        f(theta) = 2*(cl/theta)*(1-cos(theta)) + sl*sin(theta) - rail_x = 0
        안정화된 이진 탐색으로 해를 찾는다.
        """

        def f(theta):
            # theta가 0에 가까울 때의 극한값: 2*cl*(theta/2) + sl*theta - rail_x = (cl + sl)*theta - rail_x
            # 따라서 theta가 아주 작으면 f(theta)는 음수에 가까워짐.
            if theta < 1e-8:
                return -rail_x
            return 2.0 * (cl / theta) * (1.0 - math.cos(theta)) + sl * math.sin(theta) - rail_x

        low = 1e-8
        high = math.pi / 2.0  # 최대 90도 (일반적으로 분기각은 45도 이하)

        f_low = f(low)
        f_high = f(high)

        # 근이 존재하는지 확인 (부호가 달라야 함)
        if f_low * f_high > 0:
            return None

        # 이진 탐색 (100회 반복으로 충분한 정밀도 확보)
        for _ in range(100):
            mid = (low + high) / 2.0
            f_mid = f(mid)

            if abs(f_mid) < 1e-6:  # 충분히 0에 가까우면 종료
                return mid

            if f_low * f_mid < 0:
                high = mid
                f_high = f_mid
            else:
                low = mid
                f_low = f_mid

        theta = (low + high) / 2.0
        # 최종 오차 검증 (1mm 오차 허용)
        if abs(f(theta)) < 1e-3:
            return theta
        return None