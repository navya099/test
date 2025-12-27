from infrastructure.csvmanager import CSVManager
from infrastructure.filemanager import FileSystemService
from kmpost.imgdatafactory import KMImageDataFactory
from kmpost.imggeneraotr import KMImageGenerator
import os

from kmpost.systaxfactory import KMBVESyntaxFactory


class KMOutputManager:
    """KM 결과 파일, 이미지, CSV, BVE 구문 처리"""
    def __init__(self, work_directory, target_directory, offset):
        self.work_directory = work_directory
        self.target_directory = target_directory
        self.offset = offset

    def save_txt_files(self, index_datas, post_datas):
        index_file = os.path.join(self.work_directory, 'km_index.txt')
        post_file = os.path.join(self.work_directory, 'km_post.txt')
        FileSystemService.create_txt(index_file, index_datas)
        FileSystemService.create_txt(post_file, post_datas)

    def copy_result_files(self, include_ext=None, exclude_ext=None):
        FileSystemService.copy_all_files(
            self.work_directory, self.target_directory,
            include_ext or ['.csv', '.png', '.txt', '.jpg'],
            exclude_ext or ['.dxf', '.ai']
        )

    def generate_images_csv_bve(self, builder_results, source_directory, alignment_type):
        """Builder에서 생성한 sta, post_type, structure 결과를 이용해 이미지/CSV/BVE 생성"""
        index_datas= []
        post_datas = []
        kmsystaxf = KMBVESyntaxFactory()
        for i, (stadata, post_type, structure) in enumerate(builder_results):
            imgdata = KMImageDataFactory.create(post_type, stadata.after_sta, structure)
            KMImageGenerator.generate(imgdata, post_type, alignment_type, source_directory, self.work_directory)
            CSVManager.copy_and_export_csv(
                imgdata.openfile_name, imgdata.imgname, post_type,
                source_directory=source_directory,
                work_directory=self.work_directory,
                offset=self.offset
            )
            index, post = kmsystaxf.create(i=i, station=stadata, structure=structure, target_directory=self.target_directory)
            index_datas.append(index)
            post_datas.append(post)
        return index_datas, post_datas
