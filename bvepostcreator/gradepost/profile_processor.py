from dxf_manager.replacer import DXFReplacer
from gradepost.normal_post_processor import NormalGradePostCreator
from gradepost.pitch_util import get_vcurve_lines, format_grade
from gradepost.turnel_grade_post_creator import TunnelPitchCreator
from infrastructure.csvmanager import CSVManager
from infrastructure.dxftoimg import DXF2IMG
from infrastructure.structuresystem import StructureProcessor
from model.grade.vip_object_data import VIPObjectDATA
from model.grade.vipdata import VIPdata
from common.common_utils import format_distance
import os

class ProfileProcessor:
    """프로파일 처리기
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

    def build(self, start: float, end: float,vipdats: list[VIPdata], structure_processor: StructureProcessor) -> list[VIPObjectDATA]:
        """주어진 구간 정보를 처리하여 이미지 및 CSV 생성
        Arguments:
            start: 시작 측점
            end: 끝 측점
            vipdats: vip데이터 리스트
            structure_processor: 구조물 프로세서
        Returns:
            objects: 오브젝트 데이터
            """
        # 이미지 저장
        object_index = self.start_idx
        objects = []
        object_folder = self.target_directory.split("Object/")[-1]

        for i, vip in enumerate(vipdats):
            self.log(f"VIP {vip.VIPNO} 처리 중... ({i + 1}/{len(vipdats)})")
            if not start <= vip.VIP_STA <= end:
                self.log(f"범위를 벗어났습니다. 해당 구간은 건너뜁니다.")
                continue
            lines = get_vcurve_lines(vip)
            if not lines:
                continue

            # 일반철도 구배표용 구배거리
            if i < len(vipdats) - 1:
                current_distance = vipdats[i + 1].VIP_STA - vip.VIP_STA
            else:
                current_distance = 0  # 기본값 (에러 방지)

            for key, value in lines:
                current_sta = value
                current_structure = structure_processor.define_bridge_tunnel_at_station(current_sta)
                if key == 'VIP':#vip만 별도처리
                    self.process_vertical(vip, current_distance, key, current_structure)
                self.process_verticulcurve(vip, key, value)

                img_f_name = f'VIP{vip.VIPNO}_{key}'
                openfile_name = f'{key}_{current_structure}용'
                CSVManager.copy_and_export_csv(openfile_name, img_f_name, key, self.source_directory, self.work_directory)

                objects.append(
                    VIPObjectDATA(
                        no=vip.VIPNO,
                        vcurve_type=key,
                        structure=current_structure,
                        station=value,
                        object_index=object_index,
                        filename=img_f_name,
                        object_path=object_folder,
                        offset=(self.offset[current_structure][0],self.offset[current_structure][1]),
                        rotation=0
                    )
                )
                object_index += 1

        return objects

    def process_vertical(self, vip: VIPdata, current_distance: float, pitchtype: str, structure: str):
        """종곡선 없는 일간구간 처리용 메서드
        Arguments:
            vip: VIP객체
            current_distance: 현재 VIP에서 다음 VIP까지의 거리
            pitchtype: VIP타입(BVC,VIP,EVC)
            structure: 구조물
        """

        if self.al_type == '고속철도':
            return
        grade_post_generator = NormalGradePostCreator(self.work_directory)
        tunnel_post_generator = TunnelPitchCreator(self.work_directory)
        converter = DXF2IMG()

        output_image = self.work_directory + 'output_image.png'
        filename = 'BVC-수정됨.dxf'

        current_grade = vip.next_slope
        img_text2 = format_grade(current_grade)  # 기울기표 구배문자
        img_text3 = f'{int(current_distance)}'  # 기울기표 거리문자
        img_bg_color2 = (255, 255, 255)  # 기울기표 문자
        img_f_name2 = f'VIP{vip.VIPNO}_{pitchtype}_기울기표'  # 기울기표 파일명
        openfile_name2 = f'기울기표_{structure}용'

        final_output_image = self.work_directory + img_f_name2 + '.png'

        if structure == '터널' or self.al_type == '도시철도':
            tunnel_post_generator.create_tunnel_pitch_image(filename, img_text2)
            modifed_path = self.work_directory + 'BVC-수정됨.dxf'
            output_paths = converter.convert_dxf2img([modifed_path], img_format='.png')
            converter.trim_and_resize_image(output_paths[0], final_output_image, target_size=(320, 200))
        else:
            grade_post_generator.create_grade_post(img_text2, img_text3, img_f_name2, (0, 0, 0), '좌')

    def process_verticulcurve(self, vipdata: VIPdata, viptype: str, current_sta: float):
        """종곡선구간 처리용 메서드
        Arguments:
            vipdata: VIP객체
            viptype: VIP타입(BVC,VIP,EVC)
            current_sta: 현제 구간 측점
        """
        if self.al_type in ['일반철도', '도시철도']:
            #일반철도 도시철도는 종곡선 X
            return
        converter = DXF2IMG()
        if viptype == 'BVC':
            grade_text = format_grade(vipdata.prev_slope)
        elif viptype == 'VIP':
            grade_text = format_grade(vipdata.next_slope)
        elif viptype == 'EVC':
            grade_text = format_grade(vipdata.next_slope)
        else:
            grade_text = ''

        station_text = f'{format_distance(current_sta)}'

        img_f_name = f'VIP{vipdata.VIPNO}_{viptype}'
        r = str(int(vipdata.vradius))

        file_path = os.path.join(self.source_directory, f'{viptype}.dxf')
        final_output_image = os.path.join(self.work_directory, img_f_name + '.png')

        modifed_path = os.path.join(self.work_directory, 'BVC-수정됨.dxf')
        DXFReplacer.replace_text_in_dxf(file_path, modifed_path, station_text, grade_text, vipdata.seg, r)

        output_paths = converter.convert_dxf2img([modifed_path], img_format='.png')
        converter.trim_and_resize_image(output_paths[0], final_output_image, target_size=(320, 200))
