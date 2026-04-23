
import logging
from tkinter.filedialog import askopenfilename

from coord.coord_io import CoordinateLoader
from main_processor.main_processor import MainProcessor
from structure.structure_io import StructureLoader


class MainAPP:
    def __init__(self, is_cui=False, debug=False):
        self.is_cui = is_cui
        self.debug = debug
        # 역할 클래스 초기화
        self.coord_loader = CoordinateLoader()
        self.structure_loader = StructureLoader()

    def setup_logging(self):
        level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(r"c:/temp/bve_terrain_builder.log", encoding="utf-8"),
                logging.StreamHandler()
            ]
        )


    def run(self, coord_file=None, structurefilepath=None):
        self.setup_logging()
        if self.is_cui:
            self._run_cui(coord_file, structurefilepath)
        else:
            self._run_gui()

    def _run_cui(self, coord_file, structurefilepath):
        if not coord_file:
            raise ValueError('좌표파일 경로가 비어있습니다.')
        if not structurefilepath:
            raise ValueError('구조물파일 경로가 비어있습니다.')
        self._process(coord_file, structurefilepath)

    def _run_gui(self):
        coord_file = askopenfilename(title="좌표 파일 선택")
        if not coord_file:
            raise ValueError("좌표 파일을 선택하지 않았습니다.")
        structurefilepath = askopenfilename(title="구조물 파일 선택")
        if not structurefilepath:
            raise ValueError("구조물 파일을 선택하지 않았습니다.")
        self._process(coord_file, structurefilepath)

    def _process(self, coord_file, structurefilepath):
        try:
            read_coords = self.coord_loader.load(coord_file)
            structure_list = self.structure_loader.load(structurefilepath)
            mp = MainProcessor(read_coords=read_coords, structure_list=structure_list)
            mp.execute(selected_segments=[2,4])
        except Exception as e:
            logging.error(e)


