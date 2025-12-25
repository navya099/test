class KMPostProcessor:
    """처리 클래스"""

    def __init__(self):
        pass

    def process_dxf_image(self, data: BVEImageData, source_directory: str, work_directory: str, post_type: str,
                          alignmenttype: str):
        """DXF 파일 수정 및 이미지 변환"""
        file_path = source_directory + post_type + '.dxf'
        modifed_path = work_directory + post_type + '-수정됨.dxf'

        lineprogram = LineProcessor(file_path, modifed_path, data, alignmenttype)
        if post_type == 'km표':
            lineprogram.replace_text_in_dxf(mode='km')

        else:
            lineprogram.replace_text_in_dxf(mode='m')

        # 이미지 추출
        final_output_image = os.path.join(work_directory, data.imgname + '.png')
        converter = DXF2IMG()
        if alignmenttype == '도시철도':
            target_size = (200, 250)
        else:
            target_size = (180, 650)
        output_paths = converter.convert_dxf2img([modifed_path], img_format='.png')

        if output_paths:
            converter.trim_and_resize_image(output_paths[0], final_output_image, target_size)