from infrastructure.stringmanager import StringManager
from kmimg.kmimgcreator import KMImgCreator
from kmpost.kmprocessor import KMPostProcessor


class KMImageGenerator:
    @staticmethod
    def generate(imgdata, post_type, alignmenttype, source_directory, work_directory):
        if alignmenttype in ['도시철도', '일반철도']:
            KMPostProcessor().process_dxf_image(
                imgdata, source_directory, work_directory,
                post_type, alignmenttype
            )
            return

        if len(imgdata.m_string) != 1:
            imgdata.m_string = StringManager.resize_to_length(imgdata.m_string, 1)

        if post_type == 'km표':
            KMImgCreator.create_km_image(imgdata, work_directory, (500, 300), 235)
        elif post_type == 'm표' and int(imgdata.m_string) != 0:
            KMImgCreator.create_m_image(imgdata, work_directory, (250, 400), 144, 192)
