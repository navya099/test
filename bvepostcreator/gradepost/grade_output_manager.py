from model.grade.vip_object_data import VIPObjectDATA


class GradeOutputManager:
    @staticmethod
    def create_pitch_post_txt(data_list: list[VIPObjectDATA], output_file):
        """
        결과 데이터를 받아 파일로 저장하는 함수.
        """
        with open(output_file, "w", encoding="utf-8") as file:
            for data in data_list:  # 두 리스트를 동시에 순회
                file.write(
                    f"{data.station},.freeobj 0;{data.object_index};-{data.offset[0]};{data.offset[1]};{data.rotation};,;VIP{data.no}_{data.vcurve_type}-{data.structure}\n")  # 원하는 형식으로 저장

    @staticmethod
    def create_pitch_index_txt(data_list: list[VIPObjectDATA], output_file):
        """
        결과 데이터를 받아 파일로 저장하는 함수.
        """
        with open(output_file, "w", encoding="utf-8") as file:
            for data in data_list:  # 두 리스트를 동시에 순회
                file.write(f".freeobj({data.object_index}) {data.object_path}/{data.filename}.csv\n")  # 원하는 형식으로 저장