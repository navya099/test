
from core.base_runner import BaseRunner
from core.wire.wire_processor import WireProcessor

class ManualRunner(BaseRunner):
    """수동 모드용 메인러너
    Atrributes:
        offset_line_with_25: 상선 선형객체
        track_distance: 선로중심간격
        track_direction: 선로방향
        track_mode: 단선 복선 모드
        polyline_with_sta: 본선 선형객체
        pitchlist: 기울기 리스트
        curvelist: 곡선 리스트
        structure_list: 구조물 리스트[]{}
        brokenchain: 파정
    """
    def __init__(self):
        super().__init__()

    def run(self):
        self.base_info_load()
        self.create_dictionary_by_track()
        self.wire_processor = WireProcessor(self.dataprocessor, self.alignment_by_track, self.poledata, self.curvelist)
        self.log('러너 실행이 완료됐습니다. 이제 수동으로 전주를 배치하세요')