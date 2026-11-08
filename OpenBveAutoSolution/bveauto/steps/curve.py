# bveauto/steps/curve.py
from ..context import BuildContext
from ..decorators import log_errors
from ..steps.base import Step

from bve곡선레일구문생성기 import (
    preprocess_input_index, extract_cant, cal_mainlogic,
    create_freeobj, save_files, create_railtype, save_railtype,
)


class CurveStep(Step):
    name = "#2. 곡선레일"

    @log_errors("#2. 곡선레일")
    def execute(self, ctx: BuildContext, log):
        idx = preprocess_input_index(ctx.alignment_type, mode='default')
        cant = extract_cant(ctx.curve_info)
        freeobj = cal_mainlogic(ctx.curve_info, cant)

        content = create_freeobj(freeobj, ctx.structure_list, ctx.curve_info, idx)
        save_files(content, ctx.paths.route / 'freeobj.txt')

        railtype = create_railtype(ctx.curve_info, ctx.structure_list, idx)
        save_railtype(railtype, ctx.paths.route / 'railtype.txt')