class KMBVESyntaxFactory:
    def __init__(self, first_index=4025):
        self.first_index = first_index

    def create(self, i, station, structure, target_directory, track_mode, offset, track_index, track_direction):
        index = self.first_index + i
        return (
            self.create_km_index_data(index, station, target_directory),
            self.create_km_post_data(index, station, structure, track_mode, offset, track_index, track_direction)
        )

    @staticmethod
    def create_km_index_data(idx, sta, work_directory):
        object_folder = work_directory.split("Object/")[-1]
        data = f'.freeobj({idx}) {object_folder}/{sta.after_sta}.csv\n'
        return data

    @staticmethod
    def create_km_post_data(idx, sta, struc, track_mode, offset, track_index, track_direction):
        if track_mode:
            main_x = track_direction['main'] * offset[struc][0]
            main_y = offset[struc][1]
            main_rotation = 0 if track_direction['main'] == -1 else 180

            if track_mode == 'double':
                # 복선
                sub_x = track_direction['sub'] * offset[struc][0]
                sub_y = offset[struc][1]
                sub_rotation = 0 if track_direction['sub'] == -1 else 180
                data = (
                    f',;구조물={struc}\n'
                    f',;하선\n'
                    f"{sta.origin_sta},.freeobj {track_index['main']};{idx};{main_x};{main_y};{main_rotation};\n"
                    f',;상선\n'
                    f"{sta.origin_sta},.freeobj {track_index['sub']};{idx};{sub_x};{sub_y};{sub_rotation};\n"
                )
                return data
            else:
                # 단선
                return f"{sta.origin_sta},.freeobj {track_index['main']};{idx};{main_x};{main_y};{main_rotation};,;{struc}\n"
        else:
            raise ValueError(f'UNVALID track_mode')
