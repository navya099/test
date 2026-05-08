from curvepost.metro.curve_calc import CurveCalculator
from curvepost.metro.dxf_modifier import DXFModifier
from curvepost.metro.img_con import ImageConverter
import os

class CityLineProcess:
    def __init__(self, curve_type, radius, cant, tcl,
                 img_f_name, source_directory, work_directory):
        self.curve_type = curve_type
        self.radius = radius
        self.cant = cant
        self.tcl = tcl
        self.img_f_name = img_f_name
        self.source_directory = source_directory
        self.work_directory = work_directory

        self.calculator = CurveCalculator()
        self.modifier = DXFModifier()
        self.converter = ImageConverter()

    def process(self):
        speed = self.calculator.cal_speed(self.radius)
        cant_val = self.calculator.cal_cant(speed, self.radius, self.cant)
        slack_val = self.calculator.cal_slack(self.radius)

        # DXF 수정 → 이미지 변환

        file_path = os.path.join(self.source_directory, '곡선표.dxf')
        modified_path = os.path.join(self.work_directory, '곡선표-수정됨.dxf')
        if self.modifier.modify_curve_dxf(file_path, modified_path,
                                          self.curve_type, f'R={int(self.radius)}',
                                          f'C={int(cant_val)}', f'S={int(slack_val)}', self.tcl):
            self.converter.convert_and_resize(modified_path,
                                              os.path.join(self.work_directory, self.img_f_name + '.png'),
                                              (300, 210))
        # 속도제한표 처리
        if self.curve_type in ['BC', 'BCC'] and speed < 120:
            speedfile_path = os.path.join(self.source_directory, '속도제한표.dxf')
            modified_speedfile_path = os.path.join(self.work_directory, '속도제한표-수정됨.dxf')
            if self.modifier.modify_speed_limit_dxf(speedfile_path, modified_speedfile_path,
                                                    self.radius, int(speed)):
                self.converter.convert_and_resize(modified_speedfile_path,
                                                  os.path.join(self.work_directory, f'{self.img_f_name}_{int(self.radius)}.png'),
                                                  (200, 200))
