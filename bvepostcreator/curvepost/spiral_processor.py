import os

from curvepost.normal_section.normal_processor import NormalSectionProcessor
from curvepost.tunnel.tunnel_processor import TunnelProcessor
from infrastructure.dxftoimg import DXF2IMG


class SpiralProcessor:
    """완화곡선 처리용 프로세서"""
    def __init__(self, source_directory, work_directory):
        self.source_directory = source_directory
        self.work_directory = work_directory
        self.converter = DXF2IMG()
        self.tp = TunnelProcessor(self.source_directory, self.work_directory)

    def process(self, radius, img_f_name, structure):
        """DXF 파일 수정 및 이미지 변환"""
        img_f_name_for_prev = str(int(radius))
        file_path = os.path.join(self.source_directory, '곡선표.dxf')
        modifed_path = os.path.join(self.work_directory, '곡선표-수정됨.dxf')
        final_output_image = os.path.join(self.work_directory, img_f_name_for_prev + '.png')
        img_f_name_for_tunnel = f'{img_f_name}_{img_f_name_for_prev}'


        if structure == '터널':
            self.tp.process(modifed_path, img_f_name_for_prev)
            target_size = (238, 200)
        else:
            NormalSectionProcessor.processs(file_path, modifed_path, img_f_name_for_prev)
            target_size = (500, 300)

        final_output_image = os.path.join(self.work_directory, img_f_name_for_tunnel + '.png')

        output_paths = self.converter.convert_dxf2img([modifed_path], img_format='.png')

        if output_paths:
            self.converter.trim_and_resize_image(output_paths[0], final_output_image, target_size)