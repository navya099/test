
from core.airjoint.aj_data_context import AirjointDataContext
from core.airsection.as_bracket_adder import AirSectionBracketAdder
from core.equipment.equipment_data import EquipmentDATA
from core.pole.normal_section_processor import NormalSectionProcessor
from core.pole.tunnel_section_processor import TunnelSectionProcessor
from dataset.dataset_getter import DatasetGetter
from utils.math_util import calculate_curve_angle


class AirSectionProcessor:
    """에어섹션 처리용 프로세서"""
    @staticmethod
    def process(pole, polyline_with_sta, dataprocessor: DatasetGetter, idxlib, mode='single'):
        """에어섹션 구간별 전주 데이터 생성"""
        # 데이터 가져오기
        contact_wire_fitting, messenger_wire_fittings, steady_arm_fittings = dataprocessor.get_fittings()
        mast_idx = dataprocessor.get_mast_index(pole.structure, pole.section)
        mast_name = idxlib.get_name(mast_idx)
        f_bracket_valuse = dataprocessor.get_bracket_codes('F브래킷',pole.structure)
        as_bracket_values = dataprocessor.get_bracket_codes('에어섹션',pole.structure)

        # 급전선 설비 인덱스 가져오기
        feeder_idx = dataprocessor.get_feeder_insulator_idx(pole.structure)
        feeder_name =idxlib.get_name(feeder_idx)
        # 평행틀 설비 인덱스 가져오기
        length = '1.6m' if pole.section in ['에어섹션1구간_3호주', '에어섹션2구간_2호주'] else '1m'
        spreader_idx = dataprocessor.get_spreader_idx(pole.structure, length)
        spreader_name = idxlib.get_name(spreader_idx)
        #F브래킷 인상높이
        f_bracket_height = dataprocessor.get_airsection_f_bracket_height()

        # 모든 필요한 값들을 전달
        context = AirjointDataContext(
            contact_wire_fitting=contact_wire_fitting,
            messenger_wire_fittings=messenger_wire_fittings,
            steady_arm_fitting=steady_arm_fittings,
            mast_type=mast_idx,
            mast_name=mast_name,
            aj_bracket_values=as_bracket_values,
            f_bracket_valuse=f_bracket_valuse,
            feeder_idx=feeder_idx,
            feeder_name=feeder_name,
            spreader_name=spreader_name,
            spreader_idx=spreader_idx,
            f_bracket_height=f_bracket_height
        )
        # 에어섹션 구간별 처리(2호주 ,3호주, 4호주)
        adder = AirSectionBracketAdder(context, dataprocessor, idxlib, mode)
        adder.add_airsection_brackets(pole, polyline_with_sta)