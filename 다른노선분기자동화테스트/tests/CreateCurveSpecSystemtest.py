from core.component.branch_condition import BranchCondition
from core.system.create_turnout_spec import CreateTurnoutSpecSystem
from tests.create_dummy_condition import create_dummy_condition

#시스템 테스트코드
enttities, components = create_dummy_condition()
tests = CreateTurnoutSpecSystem()
tests.execute(enttities, components)