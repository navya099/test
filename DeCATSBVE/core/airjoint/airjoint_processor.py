from core.airjoint.aj_bracket_adder import AirjointBracketAdder
from core.airjoint.aj_data_context import AirjointDataContext


class AirJointProcessor:
    def __init__(self):
        self.poles = []

    def process_airjoint(self, pole, polyline_with_sta, dataprocessor, normal_processor ,idxlib):
        """에어조인트 구간별 전주 데이터 생성"""
        # 데이터 가져오기
        airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name = dataprocessor.get_fitting_and_mast_data(
            pole.structure)
        aj_bracket_values, f_bracket_valuse = dataprocessor.get_bracket_codes(pole.structure)

        # 급전선 설비 인덱스 가져오기
        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)

        # 평행틀 설비 인덱스 가져오기
        spreader_name, spreader_idx = dataprocessor.get_spreader_idx(pole.structure, pole.section)
        #F브래킷 인상높이
        f_bracket_height = dataprocessor.get_f_bracket_height()

        # 모든 필요한 값들을 전달
        context = AirjointDataContext(
            airjoint_fitting=airjoint_fitting,
            flat_fitting=flat_fitting,
            steady_arm_fitting=steady_arm_fitting,
            mast_type=mast_type,
            mast_name=mast_name,
            aj_bracket_values=aj_bracket_values,
            f_bracket_valuse=f_bracket_valuse,
            feeder_idx=feeder_idx,
            spreader_name=spreader_name,
            spreader_idx=spreader_idx,
            f_bracket_height=f_bracket_height
        )
        # 에어조인트 구간별 처리(2호주 ,3호주, 4호주)
        adder = AirjointBracketAdder(context, dataprocessor, normal_processor)
        adder.add_airjoint_brackets(pole, polyline_with_sta, idxlib)