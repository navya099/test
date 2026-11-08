# bveauto/steps/post.py
from ..context import BuildContext
from ..decorators import log_errors
from ..steps.base import Step
from ..utils import copy_post_assets

from 거리표이미지생성기 import create_km_object
from 곡선표이미지생성기 import (
    process_curve_data, create_curve_post_txt,
    create_curve_index_txt, create_speed_limit,
)
from 기울기표이미지생성기 import (
    process_and_save_sections, process_bve_profile,
    create_pitch_post_txt, create_pitch_index_txt,
)
from 교량터널구문생성기 import create_txt


class PostStep(Step):
    """km/curve/pitch 3종 포스트를 순차 생성. 각각 개별 Step으로 쪼개도 됨."""
    name = "#6. 선로제표"

    @log_errors("#6. 선로제표")
    def execute(self, ctx: BuildContext, log):
        self._km(ctx, log)
        self._curve(ctx, log)
        self._pitch(ctx, log)
        log("구조물표는 미구현 상태입니다.")

    # ---------- 거리표 ----------
    def _km(self, ctx: BuildContext, log):
        work = ctx.paths.ensure(ctx.paths.work('km_post'))
        target = ctx.paths.target('km_post')
        source = ctx.paths.source('km_post', ctx.alignment_type)

        intervel = 100 if ctx.alignment_type == '도시철도' else 200
        index_datas, post_datas = create_km_object(
            ctx.start_block, ctx.last_block, ctx.structure_list,
            intervel, ctx.alignment_type, source, work, target, ctx.offset,
        )
        create_txt(work / 'km_index.txt', index_datas)
        create_txt(work / 'km_post.txt', post_datas)

        copy_post_assets(ctx, work, source, target,
                         ['km_index.txt', 'km_post.txt'])
        log("거리표 생성 완료")

    # ---------- 곡선표 ----------
    def _curve(self, ctx: BuildContext, log):
        work = ctx.paths.ensure(ctx.paths.work('curve'))
        target = ctx.paths.target('curve_post')
        source = ctx.paths.source('curve', ctx.alignment_type)

        objectdatas = process_curve_data(
            source, work, target, ctx.curve_info, ctx.structure_list,
            ctx.brokenchain, ctx.alignment_type, 'BVE', ctx.offset,
        )
        if not objectdatas:
            log("곡선표: 생성된 객체 없음 → 건너뜀")
            return

        create_curve_post_txt(objectdatas, work / 'curve_post.txt')
        create_curve_index_txt(objectdatas, work / 'curve_index.txt')
        create_speed_limit(objectdatas, work)

        copy_post_assets(ctx, work, source, target,
                         ['curve_index.txt', 'curve_post.txt'])
        log("곡선표 생성 완료")

    # ---------- 기울기표 ----------
    def _pitch(self, ctx: BuildContext, log):
        work = ctx.paths.ensure(ctx.paths.work('pitch'))
        target = ctx.paths.target('pitch_post')
        source = ctx.paths.source('pitch', ctx.alignment_type)

        vipdatas = process_and_save_sections(
            ctx.pitch_info, ctx.brokenchain, 'BVE', ctx.pitch_info,
        )
        objectdatas = process_bve_profile(
            vipdatas, ctx.structure_list, source, work, target,
            ctx.alignment_type, offset=ctx.offset,
        )
        if not objectdatas:
            log("기울기표: 생성된 객체 없음 → 건너뜀")
            return

        create_pitch_post_txt(objectdatas, work / 'pitch_post.txt')
        create_pitch_index_txt(objectdatas, work / 'pitch_index.txt')

        copy_post_assets(ctx, work, source, target,
                         ['pitch_index.txt', 'pitch_post.txt'])
        log("기울기표 생성 완료")