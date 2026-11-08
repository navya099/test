# bveauto/steps/info.py
from ..context import BuildContext
from ..decorators import log_errors
from ..steps.base import Step

from 랜덤전주위치생성 import load_curve_data, load_pitch_data, load_coordinates
from 교량터널구문생성기 import load_structure_data


class InfoStep(Step):
    name = "#0. 기본 정보 로드"
    requires_loaded = False

    @log_errors("#0. 기본 정보 로드", reraise=True)
    def execute(self, ctx: BuildContext, log):
        log(f"설계속도={ctx.designspeed}km/h, 선로구분={ctx.alignment_type}, 선로수={ctx.linecount}")

        ctx.curve_info = load_curve_data() or []
        ctx.pitch_info = load_pitch_data() or []
        ctx.bve_coord = load_coordinates() or []
        ctx.structure_list = load_structure_data() or []

        if not ctx.curve_info:
            raise RuntimeError("곡선 정보 로드 실패")
        if not ctx.structure_list:
            raise RuntimeError("구조물 정보 로드 실패")

        ctx.start_block = ctx.curve_info[0][0]
        ctx.last_block = ctx.curve_info[-1][0]
        log(f"시작 측점: {ctx.start_block}, 끝 측점: {ctx.last_block}")
        log(f"파정: {ctx.brokenchain}, freeobj offset: {ctx.offset}")