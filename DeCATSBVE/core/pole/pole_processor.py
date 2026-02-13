from core.airjoint.airjoint_processor import AirJointProcessor
from core.airjoint.aj_checker import check_isairjoint
from core.alignment.define_funtion import iscurve, isslope
from core.bracket.bracket_data import BracketDATA
from core.pole.poledata import PoleDATA
from core.structure.define_structure import isbridge_tunnel
from dataset.dataset_getter import DatasetGetter
from utils.comom_util import generate_postnumbers, find_post_number
from utils.math_util import get_elevation_pos, interpolate_cached, calculate_offset_point


class PoleProcessor:
    def __init__(self):
        self.poles = []

    def process_pole(self, positions, structure_list, curve_list, pitchlist, dataset, airjoint_list, polyline_with_sta):
        """전주 위치 데이터를 가공 함수"""
        # 전주 데이터 구성
        pole_data = dataset['pole_data']

        # 전주번호
        post_number_lst = generate_postnumbers(positions)
        #dataset처리기
        dataprocessor = DatasetGetter(dataset)
        airjoint_processor = AirJointProcessor()
        for i in range(len(positions) - 1):
            try:
                pos, next_pos = positions[i], positions[i + 1]
                currentspan = next_pos - pos  # 전주 간 거리 계산
                # 현재 위치의 구조물 및 곡선 정보 가져오기
                current_structure = isbridge_tunnel(pos, structure_list)
                next_structure = isbridge_tunnel(next_pos, structure_list)
                current_curve, R, c = iscurve(pos, curve_list)
                current_slope, pitch = isslope(pos, pitchlist)
                z = get_elevation_pos(pos, polyline_with_sta)  # 현재 측점의 z값
                next_z = get_elevation_pos(next_pos, polyline_with_sta)  # 다음 측점의 z값
                current_airjoint = check_isairjoint(pos, airjoint_list)
                post_number = find_post_number(post_number_lst, pos)
                coord, _, v1 = interpolate_cached(polyline_with_sta, pos)

                i_type_index, o_type_index = dataprocessor.get_bracket_type(current_structure, current_curve)

                gauge = dataprocessor.get_pole_gauge(current_structure)
                next_gauge = dataprocessor.get_pole_gauge(next_structure)
                pos_coord_with_offset = calculate_offset_point(v1, coord, gauge)

                # 홀수/짝수에 맞는 전주 데이터 생성
                current_type = 'I' if i % 2 == 1 else 'O'
                next_type = 'O' if current_type == 'I' else 'I'
                pole_type = i_type_index if i % 2 == 1 else o_type_index
                bracket_name =  f"{pole_data['prefix']}-{current_type}"
                bracket = BracketDATA(bracket_type=current_type, index=pole_type, bracket_name=bracket_name)

                pole = PoleDATA(
                    pos=pos,
                    next_pos=next_pos,
                    span=currentspan,
                    gauge=gauge,
                    next_gauge=next_gauge,
                    structure=current_structure,
                    next_structure=next_structure,
                    radius=R,
                    cant=c,
                    pitch=pitch,
                    section=current_airjoint,
                    post_number=post_number,
                    brackets=[bracket],
                    mast=None,
                    equipments=[],
                    z=z,
                    next_z=next_z,
                    base_type=current_type,
                    next_base_type=next_type,
                    coord=pos_coord_with_offset
                )

                if not current_airjoint is None:
                    airjoint_processor.process_airjoint(pole, polyline_with_sta, dataprocessor)
                self.poles.append(pole)
            except Exception as e:
                print(f"process_pole 실행 중 에러 발생: {e}")
        return self.poles