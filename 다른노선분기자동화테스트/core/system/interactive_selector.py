# core/system_impl/interactive_selector.py
import math
from core.system.system import System
from core.constants import ComponentKey
from core.component.cross_turnout_spec import CrossTurnoutSpecComponent


class InteractiveSelectorSystem(System):
    """사용자에게 후보 목록을 보여주고 선택받아 최종 제원을 확정한다."""
    requires_components = frozenset({"turnout_candidates"})
    produces_components = frozenset({ComponentKey.TURNOUT_SPEC})

    def execute(self, entities, components):
        candidates = components["turnout_candidates"]

        print("\n" + "=" * 70)
        print(" 🚉 건넘선 분기기 제원 후보 목록")
        print("=" * 70)
        print(f"{'No.':<5} | {'곡선장(cl)':<10} | {'직선장(sl)':<10} | {'반지름(R)':<12} | {'접선각(θ)':<10}")
        print("-" * 70)

        for i, c in enumerate(candidates, 1):
            print(
                f"{i:<5} | {c['cl']:<10.1f} | {c['sl']:<10.1f} | {c['R']:<12.2f} | {math.degrees(c['theta']):<10.3f}°")

        print("=" * 70)

        # 사용자 입력 받기 (유효성 검사 포함)
        while True:
            try:
                choice = input(f"원하는 제원의 번호를 선택하세요 (1~{len(candidates)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(candidates):
                    selected = candidates[idx]
                    break
                else:
                    print(f"⚠️ 1에서 {len(candidates)} 사이의 숫자를 입력하세요.")
            except ValueError:
                print("⚠️ 숫자를 입력하세요.")

        # 최종 컴포넌트 생성
        spec = CrossTurnoutSpecComponent(
            start_length=selected["cl"],
            middle_length=selected["sl"],
            end_length=selected["cl"],
            cross_angle=selected["theta"],
            radius=selected["R"]
        )
        components[ComponentKey.TURNOUT_SPEC] = spec
        self.logger.info(f"사용자 선택 완료: cl={spec.start_length}, sl={spec.middle_length}, R={spec.radius:.2f}m")