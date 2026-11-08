# bveauto/steps/transmission.py
from ..context import BuildContext
from ..decorators import log_errors
from ..steps.base import Step

from 자동통신구문생성 import create_transmisson_data
from 교량터널구문생성기 import create_txt


class TransmissionStep(Step):
    name = "#5. 통신"

    @log_errors("#5. 통신")
    def execute(self, ctx: BuildContext, log):
        result = create_transmisson_data(ctx.structure_list)
        create_txt(ctx.paths.route / '통신.txt', result)