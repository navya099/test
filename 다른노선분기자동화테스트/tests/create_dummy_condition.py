from core.component.branch_condition import BranchCondition
from core.system.create_turnout_spec import CreateTurnoutSpecSystem
#시스템 테스트코드
def create_dummy_condition():
    #더미
    enttities = {}
    components = {'condition': BranchCondition(start_station=59375, end_station=59475, target_track=28)}
    return enttities, components