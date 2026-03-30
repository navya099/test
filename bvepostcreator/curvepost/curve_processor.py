from curvepost.curve_util import get_curve_lines, cal_speed
from curvepost.metro.metro_processor import CityLineProcess
from curvepost.train.train_processor import TrainProcessor
from dxf_manager.replacer import DXFReplacer
from gradepost.normal_post_processor import NormalGradePostCreator
from gradepost.pitch_util import get_vcurve_lines, format_grade
from gradepost.turnel_grade_post_creator import TunnelPitchCreator
from infrastructure.csvmanager import CSVManager
from infrastructure.dxftoimg import DXF2IMG
from infrastructure.structuresystem import StructureProcessor
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

        for i, ip in enumerate(ipdatas):
            if not start <= ip.SP_STA <= end or start <= ip.BC_STA <= end:
                print(f"범위를 벗어났습니다. 해당 구간은 건너뜁니다.")
                continue
            lines = get_curve_lines(ip)

            if not lines:
                continue

            for curvetype, station in lines:
                # 구조물 정보 확인
                is_spps = True if curvetype in ['SP', 'PS', 'BC', 'EC'] else False
                tcl = 'TCL=' + str(int(ip.PC_STA - ip.SP_STA)) if ip.curvetype == '완화곡선' else 0
                speed = int(cal_speed(ip.radius)) #곡선 제한속도 계산
                structure = structure_processor.define_bridge_tunnel_at_station(station) # 구조물(토공,교량,터널)
                img_text = format_distance(station)  # 측점문자 포맷
                img_f_name = f'IP{i + 1}_{curvetype}'  # i는 0부터임으로 1+
                openfile_name = f'{curvetype}_{structure}용'  # 소스폴더에서 열 파일명.csv원본
                if self.al_type == '도시철도':
                    citylineprocess = CityLineProcess(curvetype, ip.radius, ip.cant, tcl, img_f_name, self.source_directory, self.work_directory)
                    citylineprocess.process()

                    output_file = CSVManager.copy_and_export_csv(
                        open_filename=openfile_name,
                        output_filename=img_f_name,
                        source_directory=self.source_directory,
                        work_directory=self.work_directory,
                        replacements={
                            "LoadTexture, SP.png,": f"LoadTexture, {img_f_name}.png,",
                            "LoadTexture, R.png,": f"LoadTexture, {img_f_name}_{str(int(ip.radius))}.png,"
                        }

                    )
                    if speed < 120 and curvetype in ['BC', 'PC']:
                        CSVManager.insert_speedlimt_syntax(output_file, structure, self.source_directory)  # 속도제한표 추가
                        CSVManager.modify_r_text_in_file(output_file, img_f_name, str(int(ip.radius)))
                else:
                    #일반철도, 준고속철도
                    trainprocessor = TrainProcessor()
                    trainprocessor.process(curvetype, img_text, str(ip.cant), img_f_name, self.source_directory,
                                       self.work_directory)  # 이미지 생성 함수

                    if is_spps:#완화곡선인경우 처리
                        process_dxf_image(img_f_name, structure, ip.radius, source_directory, work_directory)
                    output_file = copy_and_export_csv(openfile_name, img_f_name, is_spps, int(ip.radius), key,
                                                      source_directory, work_directory)  # csv 원본복사 후 추출함수

                # 클래스에ㅐ 속성 추가
                objects.append(ObjectDATA(
                    IPNO=ipdatas[i].IPNO,
                    curvetype=key,
                    structure=structure,
                    station=value,
                    object_index=object_index,
                    filename=img_f_name,
                    object_path=object_folder,
                    speed=speed,
                    offset=(offset[structure][0], offset[structure][1]),
                    rotation=0
                )
                )
                object_index += 1
        return objects