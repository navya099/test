from kmpost.kmouputmanager import KMOutputManager
from model.curve.curve_object_data import CurveObjectDATA


class CURVEOutputManager(KMOutputManager):

    def create_curve_post_txt(self, data_list: list[CurveObjectDATA]):
        """
        결과 데이터를 받아 텍스트 생성하는 함수.
        """
        texts = []

        for data in data_list:
            main_x = self.track_direction['main'] * self.offset[data.structure][0]
            main_rotation = 0 if self.track_direction['main'] == -1 else 180
            main_track_idx = self.track_index['main']
            if self.track_mode == 'single':
                text = f"{data.station},.freeobj {main_track_idx};{data.object_index};{main_x};{data.offset[1]};{main_rotation};,;IP{data.no}_{data.curvetype}-{data.structure}\n"  # 원하는 형식으로 저장
                texts.append(text)
            elif self.track_mode == 'double':
                sub_x = self.track_direction['sub'] * self.offset[data.structure][0]
                sub_rotation = 0 if self.track_direction['sub'] == -1 else 180
                text1 = f"{data.station},.freeobj {self.track_index['main']};{data.object_index};{main_x};{data.offset[1]};{main_rotation};,;IP{data.no}하_{data.curvetype}-{data.structure}\n"  # 원하는 형식으로 저장
                text2 = f"{data.station},.freeobj {self.track_index['sub']};{data.object_index};{sub_x};{data.offset[1]};{sub_rotation};,;IP{data.no}상_{data.curvetype}-{data.structure}\n"  # 원하는 형식으로 저장
                texts.append(text1)
                texts.append(text2)

            else:
                raise ValueError(f'TRACK_MODE_INVALID')
        return texts

    @staticmethod
    def create_curve_index_txt(data_list: list[CurveObjectDATA], output_file):
        """
        결과 데이터를 받아 파일로 저장하는 함수.
        """
        with open(output_file, "w", encoding="utf-8") as file:
            for data in data_list:  # 두 리스트를 동시에 순회
                file.write(f".freeobj({data.object_index}) {data.object_path}/{data.filename}.csv\n")  # 원하는 형식으로 저장
