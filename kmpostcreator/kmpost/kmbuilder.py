from kmpostcreator.model.bveimgdata import BVEImageData


class KMObjectBuilder:
    """KM포스트 빌더"""
    def __init__(self, start_block, last_block, structure_list, alignmenttype, offset, interval):
        self.start_block = start_block
        self.last_block = last_block
        self.structure_list = structure_list
        self.alignmenttype = alignmenttype
        self.offset = offset
        self.interval = interval

    def define_km(self, current_sta):
        if current_sta % 1000 == 0:  # 1000의 배수이면
            post_type = 'km표'

        elif current_sta % self.interval == 0:  # 1000의 배수는 제외
            post_type = 'm표'
        else:
            post_type = ''

        return post_type

    def create_image_filename(self, post_type, current_sta, current_structure):
        # 소수점 앞뒤 자리 나누기
        current_km_int = round(current_sta * 0.001, 1)  # 소수점 3자리까지만
        km_string, m_string = f"{current_km_int:.1f}".split('.')  # 문자열로 변환 시 3자리 고정
        data = BVEImageData(
            km_string=km_string,
            m_string=m_string,
            imgname=f'{current_sta}',
            img_bg_color=(2, 6, 140),
            txt_color=(255, 255, 255),
            openfile_name=f'{post_type}_{current_structure}용'
        )
        return data

    def create_km_object(self):

        start_block = int(self.start_block // self.interval)
        last_block = int(self.last_block // self.interval)
        index_datas = []
        post_datas = []
        structure_comment=[]
        first_index = 4025

        for i in range(start_block, last_block):
            current_sta = i * self.interval
            current_structure = StructureProcessor.define_bridge_tunnel_at_station(current_sta, self.structure_list)
            post_type = self.define_km(current_sta)
            imgdata = self.create_image_filename(post_type, current_sta, current_structure)

            if self.alignmenttype in ['도시철도', '일반철도']:
                dxfprocs = KMPostProcessor()
                dxfprocs.process_dxf_image(imgdata, source_directory, work_directory, post_type, self.alignmenttype)
            else:
                if len(imgdata.m_string) !=1 :#글자수가 1이 아니면 강제로 1로 적용 예)60 >6
                   imgdata.m_string = resize_to_length(imgdata.m_string, desired_length=1)
                if post_type == 'km표':
                    create_km_image(imgdata, work_directory, image_size=(500, 300), font_size=235)

                elif post_type == 'm표':
                    if int(imgdata.m_string) != 0:
                        create_m_image(imgdata, work_directory, image_size=(250, 400), font_size=144, font_size2=192)

            #텍스쳐와 오브젝트 csv생성
            copy_and_export_csv(imgdata.openfile_name, imgdata.imgname, post_type, source_directory, work_directory ,offset)

            index = first_index + i

            #구문데이터 생성
            index_data = create_km_index_data(index , current_sta, target_directory)
            post_data = create_km_post_data(index , current_sta, current_structure)

            #리스트에 추가
            index_datas.append(index_data)
            post_datas.append(post_data)

        print("\n구문 생성 완료!")
        print("\n이미지 생성 완료!")


        return index_datas, post_datas