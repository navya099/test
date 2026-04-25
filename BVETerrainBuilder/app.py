
import logging
from tkinter.filedialog import askopenfilename

from alignment.parser import AlignmentParser
from coord.coord_io import CoordinateLoader
from file_manager.file_controller import FileController
from main_processor.main_processor import MainProcessor
from structure.structure_io import StructureLoader
from track.railloader import RailLoader
from ui.main_ui import MainGUI


class MainAPP:
    def __init__(self, is_cui=False, debug=False):
        self.is_cui = is_cui
        self.debug = debug
        # 역할 클래스 초기화
        self.coord_loader = CoordinateLoader()
        self.structure_loader = StructureLoader()
        self.rail_loader = AlignmentParser()
        self.file_loader = FileController()

    def setup_logging(self):
        level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(r"c:/temp/bve_terrain_builder.log", encoding="utf-8", mode='w'),
                logging.StreamHandler()
            ]
        )

    def run(self):
        # GUI 인스턴스 생성 및 실행
        self.gui = MainGUI(self._process_callback)
        self.gui.run()

    def _process_callback(self, coord_path, struct_path, rail_path, selected_segs, is_visible):
        # GUI에서 넘겨받은 파라미터로 실제 프로세스 실행
        self._process(coord_path, struct_path, rail_path, selected_segs, is_visible)

    def _process(self, coord_file, structurefilepath, rail_info_path, selected_segs=[16], is_visible=True):
        self.setup_logging()  # 로그 설정 적용
        try:
            read_coords = self.coord_loader.load(coord_file)
            structure_list = self.structure_loader.load(structurefilepath)

            # rail_info_path가 있을 때만 파싱
            tracks = None
            if rail_info_path:
                content = self.file_loader.read_file(rail_info_path)
                tracks = self.rail_loader.process_lines_to_alginment_data(content)

            mp = MainProcessor(read_coords=read_coords, structure_list=structure_list, tracks=tracks)
            # GUI에서 선택한 세그먼트와 시각화 여부 적용
            mp.execute(selected_segments=selected_segs, is_visible=is_visible)

        except Exception as e:
            logging.error(f"프로세스 실행 중 치명적 오류: {e}")
            raise e


