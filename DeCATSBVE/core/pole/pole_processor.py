from core.airjoint.airjoint_processor import AirJointProcessor
from core.airjoint.aj_checker import check_isairjoint
from core.alignment.define_funtion import iscurve, isslope
from core.bracket.bracket_data import BracketDATA
from core.pole.normal_section_processor import NormalSectionProcessor
from core.pole.poledata import PoleDATA
from core.structure.define_structure import isbridge_tunnel
from dataset.dataset_getter import DatasetGetter
from utils.comom_util import generate_postnumbers, find_post_number
from utils.math_util import get_elevation_pos, interpolate_cached, calculate_offset_point

class PoleProcessor:
    def __init__(self):
        self.poles = []

    def _process_single_track(self, positions, structure_list, curve_list, pitchlist,
                              dataprocessor, airjoint_list, polyline_with_sta, idxlib,
                              track_name="main", side="L"):
        """단일 트랙 처리 함수"""
        post_number_lst = generate_postnumbers(positions)
        airjoint_processor = AirJointProcessor()
        normal_processor = NormalSectionProcessor()
        poles = []

        for i in range(len(positions) - 1):
            try:
                pos, next_pos = positions[i], positions[i + 1]
                currentspan = next_pos - pos
                current_structure = isbridge_tunnel(pos, structure_list)
                next_structure = isbridge_tunnel(next_pos, structure_list)
                current_curve, R, c = iscurve(pos, curve_list)
                current_slope, pitch = isslope(pos, pitchlist)
                z = get_elevation_pos(pos, polyline_with_sta)
                next_z = get_elevation_pos(next_pos, polyline_with_sta)
                current_airjoint = check_isairjoint(pos, airjoint_list)
                post_number = find_post_number(post_number_lst, pos)
                coord, _, v1 = interpolate_cached(polyline_with_sta, pos)

                gauge = dataprocessor.get_pole_gauge(current_structure)
                next_gauge = dataprocessor.get_pole_gauge(next_structure)
                if side == 'L':
                    gauge *= -1
                    next_gauge *= -1
                    current_type = 'I' if i % 2 == 1 else 'O'
                    next_type = 'O' if current_type == 'I' else 'I'
                else:
                    current_type = 'O' if i % 2 == 1 else 'I'
                    next_type = 'I' if current_type == 'O' else 'O'
                pos_coord_with_offset = calculate_offset_point(v1, coord, gauge)

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
                    brackets=[],
                    mast=None,
                    equipments=[],
                    z=z,
                    next_z=next_z,
                    base_type=current_type,
                    next_base_type=next_type,
                    coord=pos_coord_with_offset,
                    track=track_name,  # 추가
                    side=side  # 추가
                )
                if current_airjoint is None:
                    normal_processor.process(pole, dataprocessor, idxlib)
                else:
                    airjoint_processor.process_airjoint(pole, polyline_with_sta,
                                                        dataprocessor, normal_processor, idxlib)
                poles.append(pole)
            except Exception as e:
                print(f"[{track_name}] process_pole 실행 중 에러 발생: {e}")
        return poles

    def process_pole_multitrack(self, positions_by_track, structure_list_by_track,
                                curve_list_by_track, pitchlist_by_track,
                                dataprocessor, airjoint_list, polyline_with_sta,
                                idxlib, track_mode="single", track_direction="L"):
        """단일/이중 트랙 모두 지원"""
        results = {}
        if track_mode == "single":
            results["main"] = self._process_single_track(
                positions_by_track["main"],
                structure_list_by_track["main"],
                curve_list_by_track["main"],
                pitchlist_by_track["main"],
                dataprocessor, airjoint_list, polyline_with_sta['main'], idxlib,
                track_name="main", side=track_direction
            )
        else:  # double track
            if track_direction == "mainL_subR":
                results["main"] = self._process_single_track(
                    positions_by_track["main"],
                    structure_list_by_track["main"],
                    curve_list_by_track["main"],
                    pitchlist_by_track["main"],
                    dataprocessor, airjoint_list, polyline_with_sta['main'], idxlib,
                    track_name="main", side="L"
                )
                results["sub"] = self._process_single_track(
                    positions_by_track["sub"],
                    structure_list_by_track["sub"],
                    curve_list_by_track["sub"],
                    pitchlist_by_track["sub"],
                    dataprocessor, airjoint_list, polyline_with_sta['sub'], idxlib,
                    track_name="sub", side="R"
                )
            else:  # mainR_subL
                results["main"] = self._process_single_track(
                    positions_by_track["main"],
                    structure_list_by_track["main"],
                    curve_list_by_track["main"],
                    pitchlist_by_track["main"],
                    dataprocessor, airjoint_list, polyline_with_sta, idxlib,
                    track_name="main", side="R"
                )
                results["sub"] = self._process_single_track(
                    positions_by_track["sub"],
                    structure_list_by_track["sub"],
                    curve_list_by_track["sub"],
                    pitchlist_by_track["sub"],
                    dataprocessor, airjoint_list, polyline_with_sta, idxlib,
                    track_name="sub", side="L"
                )
        return results