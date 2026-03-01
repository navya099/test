from core.alignment.define_funtion import iscurve, isslope
from core.pole.normal_section_processor import NormalSectionProcessor
from core.pole.poledata import PoleDATA
from utils.math_util import get_elevation_pos, interpolate_cached, calculate_offset_point


class ManualPoleProcessor:
    """단일 전주 생성기"""
    @staticmethod
    def create_pole(alignment, db, idxlib ,curvelist, pitchlist, pos, post_number, gauge, structure, section, base_type, track="main", side="L"):
        """단일 전주 생성 메서드
        Args:
            alignment: 선형객체
            curvelist: 곡선 리스트
            pitchlist: 구배 리스트
            pos: 측점
            post_number: 전주번호
            gauge: 건식게이지
            structure: 구조물 str
            section: 구간 str
            base_type: 기본타입 I, O ,F
            track: 트랙 구분 main or sub
            side: 트랙사이드 L, R
        return:
            PoleDATA
        """

        z = get_elevation_pos(pos, alignment)
        current_curve, R, c = iscurve(pos, curvelist)
        current_slope, pitch = isslope(pos, pitchlist)
        coord, _, v1 = interpolate_cached(alignment, pos)
        pos_coord_with_offset = calculate_offset_point(v1, coord, gauge)

        # PoleDATA 객체 생성
        pole = PoleDATA(
            pos=pos,
            next_pos=None,
            span=None,
            gauge=gauge,
            next_gauge=None,
            structure=structure,
            next_structure=None,
            radius=R,
            cant=c,
            pitch=pitch,
            section=section,
            post_number=post_number,
            brackets=[],
            mast=None,
            equipments=[],
            z=z,
            next_z=None,
            base_type=base_type,
            next_base_type=None,
            coord=pos_coord_with_offset,
            track=track,
            side=side
        )
        NormalSectionProcessor.process(pole, db, idxlib)
        return pole