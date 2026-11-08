# bveauto/steps/pole.py
from ..context import BuildContext
from ..decorators import log_errors
from ..steps.base import Step

from 랜덤전주위치생성 import (
    distribute_pole_spacing_flexible, define_airjoint_section,
    generate_postnumbers, load_dataset, PoleProcessor, WireProcessor,
    DatasetGetter, BVECSV, write_to_file,
)


class PoleStep(Step):
    name = "#3. 전차선"

    @log_errors("#3. 전차선")
    def execute(self, ctx: BuildContext, log):
        end_km = int(ctx.last_block // 1000)
        spans, pole_positions = distribute_pole_spacing_flexible(0, end_km)

        airjoint_list = define_airjoint_section(pole_positions, airjoint_span=1600)
        polyline = [(i * 25, *v) for i, v in enumerate(ctx.bve_coord)]
        post_numbers = generate_postnumbers(pole_positions)

        dataset = load_dataset(ctx.designspeed, ctx.iscustommode)
        getter = DatasetGetter(dataset)

        processor = PoleProcessor()
        poledata = processor.process_pole(
            pole_positions, ctx.structure_list, ctx.curve_info,
            ctx.pitch_info, dataset, airjoint_list, polyline,
        )
        wire = WireProcessor(getter, polyline, poledata).process_to_wire()
        saver = BVECSV(poledata, wire)

        write_to_file(ctx.paths.route / '전주.txt', saver.create_pole_csv())
        write_to_file(ctx.paths.route / '전차선.txt', saver.create_wire_csv())

        log(f"전주 {len(pole_positions)}개, 에어조인트 {len(airjoint_list)}구간")