from tkinter.filedialog import askopenfilename

from alignment.calculoatr import AlignmentCalculator
from alignment.parser import AlignmentParser
from coord.coord_io import CoordinateLoader
import logging as log

from core.component.branch_condition import BranchCondition
from core.system.calculator_angle import CalculateAngleSystem
from core.system.create_turnout_spec import CreateTurnoutSpecSystem
from core.system.curve_calculator import CurveCalculatorSystem
from core.system.extract_start_info import ExtractStartInfoSystem
from core.system.get_target_track import GetTargetTrackSystem
from core.world.world import World
from file_manager.file_controller import FileController


class Main:
    def __init__(self):
        self.rail_loader = AlignmentParser()
        self.file_loader = FileController()
        self.coord_file = None
        self.mainlineloader = CoordinateLoader()
        self.tracks = None
        self.rail_info_path = None
        log.basicConfig(
            level=log.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
    def main(self):
        # 1. 자선 선형 로드
        self.coord_file = askopenfilename(title='자선 좌표파일 선택')
        if not self.coord_file:
            log.warning('자선 파일이 선택되지 않았습니다.')
            return
        coords = self.mainlineloader.load(self.coord_file)

        # 2. 정거장 파일 로드
        self.rail_info_path = askopenfilename(title='정거장 파일 선택')
        if not self.rail_info_path:
            log.warning('정거장 파일이 선택되지 않았습니다.')
            return
        content = self.file_loader.read_file(self.rail_info_path)
        self.tracks = self.rail_loader.process_lines_to_alginment_data(content)

        #3. 선형 생성
        al_cal_pm = AlignmentCalculator()
        self.tracks.insert(0, al_cal_pm.create_mainline(coords))
        # 다른 트랙들 선형 생성
        al_cal_pm.calculate_otherline_coordinates(self.tracks)

        # 3. ECS 패턴 적용
        world = World()
        world.add_entity("coords", coords)
        world.add_entity("tracks", self.tracks)

        #자선 엔티티 등록
        main_alignment = next((a for a in self.tracks if a.name == '자선'), None)
        if main_alignment:
            world.add_entity("main_alignment", main_alignment)

        #자선분기 조건 컴포넌트
        branch_condition = BranchCondition(start_station=59375, end_station=59475, target_track=28)
        world.add_component("branch_condition", branch_condition)

        # 시스템 등록
        world.add_system(ExtractStartInfoSystem()) #시작정보 추출 시스템
        world.add_system(CreateTurnoutSpecSystem())  # 분기기 제원 계산
        world.add_system(GetTargetTrackSystem())  #대상 트랙 찾기
        world.add_system(CalculateAngleSystem())  #분기각 계산
        world.add_system(CurveCalculatorSystem()) #곡선재원 산출
        # 실행
        world.run()


if __name__ == '__main__':
    main = Main()
    main.main()