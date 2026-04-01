from curvepost.curve_util import get_curve_lines, cal_speed
from curvepost.metro.metro_processor import CityLineProcess
from curvepost.spiral_processor import SpiralProcessor
from curvepost.train.train_processor import TrainProcessor
from dxf_manager.replacer import DXFReplacer
from gradepost.normal_post_processor import NormalGradePostCreator
from gradepost.pitch_util import get_vcurve_lines, format_grade
from gradepost.turnel_grade_post_creator import TunnelPitchCreator
from infrastructure.csvmanager import CSVManager
from infrastructure.dxftoimg import DXF2IMG
from infrastructure.structuresystem import StructureProcessor
from model.curve.curve_object_data import CurveObjectDATA
from model.curve.ipdata import IPdata
from model.grade.vip_object_data import VIPObjectDATA
from model.grade.vipdata import VIPdata
from common.common_utils import format_distance
import os

class CurveProcessor:
    """곡선 처리기
    Attributes:
        source_directory: 소스 폴더
        work_directory: 작업 폴더
        target_directory: 대상 폴더
        al_type: 선로 종류(일반철도, 도시철도, 고속철도, 준고속철도)
        offset: 구조물별 오프셋 딕셔너리
        log: 로그
    """
    def __init__(self, source_directory, work_directory, target_directory, al_type, offset, start_idx, log):
        self.source_directory = source_directory
        self.work_directory = work_directory
        self.target_directory = target_directory
        self.al_type = al_type
        self.offset = offset
        self.start_idx = start_idx
        self.log = log

    def build(self, start: float, end: float, ipdatas: list[IPdata], structure_processor: StructureProcessor) -> list[VIPObjectDATA]:
        """주어진 구간 정보를 처리하여 이미지 및 CSV 생성"""

        object_index = self.start_idx
        objects = []
        object_folder = self.target_directory.split("Object/")[-1]

        ipdatas = self.filter_ipdatas(ipdatas, start, end) #범위 필터링
        for i, (ip, lines) in enumerate(ipdatas):
            for curvetype, station in lines:
                structure = structure_processor.define_bridge_tunnel_at_station(station) # 구조물(토공,교량,터널)
                station_text = format_distance(station)  # 측점문자 포맷
                img_f_name = f'IP{i + 1}_{curvetype}'  # 생성할 이미지명. i는 0부터임으로 1+
                openfile_name = f'{curvetype}_{structure}용'  # 소스폴더에서 열 파일명.csv원본
                speed = int(cal_speed(ip.radius))

                if self.al_type == '도시철도':
                    self.process_cityline(ip, curvetype, img_f_name, openfile_name, structure, speed)
                else:
                    self.process_trainline(ip, curvetype, station_text,img_f_name, openfile_name, structure)
                csvobject = self.create_curve_object(ip, curvetype,structure, station,object_index, img_f_name, object_folder,speed)
                objects.append(csvobject)
                object_index += 1
        return objects

    def call_copy_and_export(self, openfile_name, img_f_name, curvetype, radius):
        return CSVManager.copy_and_export_csv(
            openfile_name,
            img_f_name,
            self.source_directory,
            self.work_directory,
            replacements={
                f"LoadTexture, {curvetype}.png,": f"LoadTexture, {img_f_name}.png,",
                f"LoadTexture, R.png,": f"LoadTexture, {img_f_name}_{int(radius)}.png,"
            })  # csv 원본복사 후 추출함수

    def filter_ipdatas(self, ipdatas, start, end):
        """범위 필터링"""
        valid_ips = []
        for ip in ipdatas:
            # SP, BC 둘 다 None이면 무효
            if ip.SP_STA is None and ip.BC_STA is None:
                self.log("STA 값 없음")
                continue

            sp_in_range = (ip.SP_STA is not None and start <= ip.SP_STA <= end)
            bc_in_range = (ip.BC_STA is not None and start <= ip.BC_STA <= end)

            # 둘 중 하나라도 범위 안에 있으면 유효
            if not (sp_in_range or bc_in_range):
                self.log("범위를 벗어났습니다.")
                continue

            lines = get_curve_lines(ip)
            if not lines:
                self.log("데이터 없음")
                continue

            valid_ips.append((ip, lines))
        return valid_ips

    def process_cityline(self, ip, curvetype, img_f_name, openfile_name, structure, speed):
          # 곡선 제한속도 계산
        tcl = 'TCL=' + str(int(ip.PC_STA - ip.SP_STA)) if ip.curvetype == '완화곡선' else 0
        citylineprocess = CityLineProcess(curvetype, ip.radius, ip.cant, tcl,img_f_name, self.source_directory,
                                          self.work_directory)
        citylineprocess.process()
        output_file = self.call_copy_and_export(openfile_name, img_f_name, curvetype, ip.radius)
        if speed < 120 and curvetype in ['BC', 'PC']:
            add_file = os.path.join(self.source_directory, f'속도제한표-{structure}용.csv')
            CSVManager.insert_other_text(output_file, add_file)
        return output_file

    def process_trainline(self, ip, curvetype, img_text, img_f_name, openfile_name, structure):
        trainprocessor = TrainProcessor()
        trainprocessor.process(curvetype, img_text, str(ip.cant), img_f_name, self.source_directory,
                               self.work_directory)
        if curvetype in ['SP', 'PS', 'BC', 'EC']:
            spiral_processor = SpiralProcessor(self.source_directory, self.work_directory)
            spiral_processor.process(ip.radius, img_f_name, structure)
        output_file =self.call_copy_and_export(openfile_name, img_f_name, curvetype, ip.radius)
        return output_file

    def create_curve_object(self, ip, curvetype, structure, station, object_index, img_f_name, object_folder, speed):
        return CurveObjectDATA(
            no=ip.IPNO,
            curvetype=curvetype,
            structure=structure,
            station=station,
            object_index=object_index,
            filename=img_f_name,
            object_path=object_folder,
            speed=speed,
            offset=(self.offset[structure][0], self.offset[structure][1]),
            rotation=0
        )