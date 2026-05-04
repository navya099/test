from core.component.cross_turnout_spec import CrossTurnoutSpecComponent
from core.system.system import System
import logging

class CreateTurnoutSpecSystem(System):
    """자선분기 조건으로부터 분기기 제원 생성"""
    def execute(self, entities, components):
        condition = components['branch_condition']
        length = condition.length

        # 가능한 접선장 후보 (12.5 배수)
        step = 125  # 12.5 * 10
        tl_options = [i / 10 for i in range(0, int(length * 10) + 1, step)]
        find = None
        turnout_spec = None
        for cl in tl_options:
            if find: break
            if cl < 25: continue #곡선장은 25의 배수여야함
            if cl % 25 != 0: continue
            for sl in tl_options:
                if find: break
                if sl < 25: continue  # sl은 반드시 25의 배수
                if sl % 25 != 0: continue
                if cl*2 + sl == length:
                    turnout_spec = CrossTurnoutSpecComponent(
                        start_length=cl, middle_length=sl, end_length=cl)
                    components['turnout_spec'] = turnout_spec
                    find = True
                    logging.info(f'[CreateTurnoutSpecSystem]: find turnout_spec at '
                                 f'start_length={getattr(turnout_spec, "start_length")}, '
                                 f'middle_length={getattr(turnout_spec, "middle_length")}, '
                                 f'end_length={getattr(turnout_spec, "end_length")}')


