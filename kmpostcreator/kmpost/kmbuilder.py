from infrastructure.csvmanager import CSVManager
from infrastructure.structuresystem import StructureProcessor
from kmpost.imgdatafactory import KMImageDataFactory
from kmpost.imggeneraotr import KMImageGenerator
from kmpost.systaxfactory import KMBVESyntaxFactory
from kmpost.typeresolver import KMPostTypeResolver
from model.bveimgdata import BVEImageData


class KMObjectBuilder:
    """KM포스트 빌더"""
    def __init__(self, start_block, last_block, structure_list, alignmenttype, offset, interval ,source_directory, work_directory, target_directory):
        self.start_block = start_block
        self.last_block = last_block
        self.structure_list = structure_list
        self.alignmenttype = alignmenttype
        self.offset = offset
        self.interval = interval
        self.source_directory = source_directory
        self.work_directory = work_directory
        self.target_directory = target_directory

        self.type_resolver = KMPostTypeResolver(interval)
        self.image_factory = KMImageDataFactory()
        self.image_generator = KMImageGenerator()
        self.syntax_factory = KMBVESyntaxFactory()

    def run(self):
        index_datas, post_datas = [], []

        for i in range(
            int(self.start_block // self.interval),
            int(self.last_block // self.interval)
        ):
            sta = i * self.interval
            structure = StructureProcessor.define_bridge_tunnel_at_station(
                sta, self.structure_list
            )
            post_type = self.type_resolver.resolve(sta)

            if not post_type:
                continue

            imgdata = self.image_factory.create(post_type, sta, structure)
            self.image_generator.generate(imgdata, post_type, self.alignmenttype, self.source_directory, self.work_directory)
            CSVManager.copy_and_export_csv(
                imgdata.openfile_name, imgdata.imgname, post_type,
                source_directory=self.source_directory,
                work_directory=self.work_directory,
                offset=self.offset)

            index, post = self.syntax_factory.create(i, sta, structure, self.target_directory)
            index_datas.append(index)
            post_datas.append(post)

        print("✅ 구문 및 이미지 생성 완료")
        return index_datas, post_datas
