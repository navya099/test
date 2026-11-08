# bveauto/steps/bridge.py
from ..context import BuildContext
from ..decorators import log_errors
from ..steps.base import Step

from 교량터널구문생성기 import create_network_data, create_txt


class BridgeStep(Step):
    name = "#1. 교량/터널 구조물"

    @log_errors("#1. 교량/터널 구조물")
    def execute(self, ctx: BuildContext, log):
        result = create_network_data(ctx.structure_list, ctx.designspeed, ctx.linecount)
        create_txt(ctx.paths.route / '구조물.txt', result)