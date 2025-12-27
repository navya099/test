from infrastructure.dxftoimg import DXF2IMG
from kmpost.lineprocessor import LineProcessor
from model.bveimgdata import BVEImageData
import os

class KMPostProcessor:
    """DXF 수정 및 이미지 변환"""

    @staticmethod
    def process_dxf_image(
        data: BVEImageData,
        source_directory: str,
        work_directory: str,
        post_type: str,
        alignmenttype: str
    ):
        file_path = os.path.join(source_directory, f'{post_type}.dxf')
        modified_path = os.path.join(work_directory, f'{post_type}-수정됨.dxf')

        lineprogram = LineProcessor(file_path, modified_path, data, alignmenttype)
        mode = 'km' if post_type == 'km표' else 'm'
        lineprogram.replace_text_in_dxf(mode=mode)

        converter = DXF2IMG()
        output_paths = converter.convert_dxf2img([modified_path], img_format='.png')

        if not output_paths:
            return

        final_image = os.path.join(work_directory, f'{data.imgname}.png')

        target_size = (200, 250) if alignmenttype == '도시철도' else (180, 650)
        converter.trim_and_resize_image(output_paths[0], final_image, target_size)
