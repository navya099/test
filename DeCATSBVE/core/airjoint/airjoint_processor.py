from core.airjoint.aj_bracket_adder import AirjointBracketAdder
from core.airjoint.aj_data_context import AirjointDataContext


class AirJointProcessor:
    @staticmethod
    def process(pole, polyline_with_sta, dataprocessor, idxlib):
        """에어조인트 구간별 전주 데이터 생성"""
        # 데이터 가져오기
        contact_wire_fitting, messenger_wire_fittings, steady_arm_fittings = dataprocessor.get_fittings()
        mast_idx = dataprocessor.get_mast_index(pole.structure)
        mast_name = idxlib.get_name(mast_idx)
        f_bracket_valuse = dataprocessor.get_bracket_codes(pole.structure, type='F')
        aj_bracket_values = dataprocessor.get_bracket_codes(pole.structure, type='AJ')

        # 급전선 설비 인덱스 가져오기
        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)
        feeder_name =idxlib.get_name(feeder_idx)
        # 평행틀 설비 인덱스 가져오기
        spreader_idx = dataprocessor.get_spreader_idx(pole.structure, pole.section)
        spreader_name = idxlib.get_name(spreader_idx)
        #F브래킷 인상높이
        f_bracket_height = dataprocessor.get_f_bracket_height()

        # 모든 필요한 값들을 전달
        context = AirjointDataContext(
            contact_wire_fitting=contact_wire_fitting,
            messenger_wire_fittings=messenger_wire_fittings,
            steady_arm_fitting=steady_arm_fittings,
            mast_type=mast_idx,
            mast_name=mast_name,
            aj_bracket_values=aj_bracket_values,
            f_bracket_valuse=f_bracket_valuse,
            feeder_idx=feeder_idx,
            feeder_name=feeder_name,
            spreader_name=spreader_name,
            spreader_idx=spreader_idx,
            f_bracket_height=f_bracket_height
        )
        # 에어조인트 구간별 처리(2호주 ,3호주, 4호주)
        adder = AirjointBracketAdder(context, dataprocessor)
        adder.add_airjoint_brackets(pole, polyline_with_sta, idxlib)