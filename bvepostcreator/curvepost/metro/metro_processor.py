#도시철도용 곡선처리
import ezdxf
import os

from infrastructure.dxftoimg import DXF2IMG
from model.curve.ipdata import IPdata


class CityLineProcess:
    """도시철도용 곡선표 처리기
    Attributes:
        curve_type: 곡선 타입[BTC,BCC,ECC,ETC]
        radius: 곡선반경
        cant: 캔트
        tcl: 완화곡선장
        img_f_name: 이미지 이름
        source_directory: 소스 디렉터리
        work_directory: RESULT폴더

    """
    def __init__(self, curve_type: str, radius: float, cant: float, tcl: int,
                    img_f_name: str, source_directory: str, work_directory: str):
        self.curve_type = curve_type
        self.radius = radius
        self.cant = cant
        self.tcl = tcl
        self.img_f_name = img_f_name
        self.source_directory = source_directory
        self.work_directory = work_directory

    def process(self):
        """메인 프로세서"""
        curve_map = {
            'SP': 'BTC', 'PC': 'BCC', 'CP': 'ECC', 'PS': 'ETC',
            'BC': 'BC', 'EC': 'EC'
        }
        new_curve_type = curve_map.get(self.curve_type, None)

        speed = self.cal_speed()
        cant_val = self.cal_cant(speed, self.radius, self.cant)

        r_text = f'R={int(self.radius)}'
        c_text = f'C={int(cant_val)}'
        s_text = f'S={int(self.cal_slack())}'

        file_path = os.path.join(self.source_directory, '곡선표.dxf')
        modified_path = os.path.join(self.work_directory, '곡선표-수정됨.dxf')
        speedfile_path = os.path.join(self.source_directory, '속도제한표.dxf')
        modified_speedfile_path = os.path.join(self.work_directory, '속도제한표-수정됨.dxf')

        img_f_name_for_speed = f'{self.img_f_name}_{int(self.radius)}'
        final_output_image = os.path.join(self.work_directory, self.img_f_name + '.png')
        speedlimit_image = os.path.join(self.work_directory, img_f_name_for_speed + '.png')

        converter = DXF2IMG()

        if self.modify_dxf(file_path, modified_path, new_curve_type, r_text, c_text, s_text, self.tcl):
            output_paths = converter.convert_dxf2img([modified_path], img_format='.png')
            if output_paths:
                converter.trim_and_resize_image(output_paths[0], final_output_image, (300, 210))

        if new_curve_type in ['BC', 'BCC']:
            if speed < 120:
                if self.process_speed_limit_post(speedfile_path, modified_speedfile_path, self.radius, int(speed)):
                    output_paths = converter.convert_dxf2img([modified_speedfile_path], img_format='.png')
                    if output_paths:
                        converter.trim_and_resize_image(output_paths[0], speedlimit_image, (200, 200))


    def cal_slack(self) -> float:
        """슬랙 계산"""
        slack = 2400 / self.radius
        return slack - 5 if slack >= 30 else slack

    def cal_speed(self) -> float:
        """곡선속도 계산"""
        return (self.radius * 160 / 11.8) ** 0.5

    def cal_cant(self, speed: float, radius: float, original_cant: float) -> float:
        """캔트 계산"""
        if original_cant == 0:
            value = 11.8 * (speed ** 2) / radius
            return min(value, 160)
        return original_cant

    def modify_dxf(self,origin_file_path: str, new_file_path: str,
                   current_curve_type: str, current_radius: str,
                   current_cant: str, slack: str, tcl_value: int) -> bool:
        """dxf 수정 메서드"""
        try:
            doc = ezdxf.readfile(origin_file_path)
            msp = doc.modelspace()
            layers = doc.layers

            if current_curve_type in ['BTC', 'BCC', 'ECC', 'ETC']:
                layers.get('제원문자-앞').on()
                layers.get('제원문자-중간').on()
                layers.get('제원문자-뒤').on()
            elif current_curve_type in ['BC', 'EC']:
                layers.get('제원문자-앞').on()
                layers.get('제원문자-뒤').on()

            for entity in msp.query("TEXT"):
                if current_curve_type in ['BTC', 'BCC', 'ECC', 'ETC']:
                    if entity.dxf.layer == "제원문자-앞":
                        entity.dxf.text = current_curve_type[0]
                    elif entity.dxf.layer == "제원문자-중간":
                        entity.dxf.text = current_curve_type[1]
                    elif entity.dxf.layer == "제원문자-뒤":
                        entity.dxf.text = current_curve_type[2]
                elif current_curve_type in ['BC', 'EC']:
                    if entity.dxf.layer == "제원문자-앞":
                        entity.dxf.text = current_curve_type[0]
                    elif entity.dxf.layer == "제원문자-뒤":
                        entity.dxf.text = current_curve_type[1]

                if current_curve_type in ['BCC', 'BC', 'EC', 'ECC']:
                    layers.get('R').on()
                    layers.get('C').on()
                    layers.get('S').on()

                    if entity.dxf.layer == "R":
                        entity.dxf.text = current_radius
                    elif entity.dxf.layer == "C":
                        entity.dxf.text = current_cant
                    elif entity.dxf.layer == "S":
                        entity.dxf.text = slack
                elif current_curve_type in ['BTC', 'ETC']:
                    layers.get('TCL').on()
                    if entity.dxf.layer == "TCL":
                        entity.dxf.text = str(tcl_value)

            doc.saveas(new_file_path)

            return True

        except Exception as e:
            print(f"❌ DXF 텍스트 교체 실패: {e}")
            return False

    def process_speed_limit_post(self, speedfile_path: str, modified_speedfile_path: str,
                                 radius: float, speed_value: int) -> bool:
        """속도제한표 이미지 생성"""
        try:
            doc = ezdxf.readfile(speedfile_path)
            msp = doc.modelspace()

            for entity in msp.query("TEXT"):
                if entity.dxf.layer == "V":
                    entity.dxf.text = str(speed_value)
                if entity.dxf.layer == "R":
                    entity.dxf.text = str(int(radius))

            doc.saveas(modified_speedfile_path)

            return True

        except Exception as e:
            print(f"❌ 속도 제한 DXF 텍스트 교체 실패: {e}")
            return False

