class KMBVESyntaxFactory:
    def __init__(self, first_index=4025):
        self.first_index = first_index

    def create(self, i, station, structure, target_directory):
        index = self.first_index + i
        return (
            self.create_km_index_data(index, station, target_directory),
            self.create_km_post_data(index, station, structure)
        )

    @staticmethod
    def create_km_index_data(idx, sta, work_directory):
        object_folder = work_directory.split("Object/")[-1]
        data = f'.freeobj({idx}) {object_folder}/{sta.after_sta}.csv\n'
        return data

    @staticmethod
    def create_km_post_data(idx, sta, struc):
        data = f'{sta.origin_sta},.freeobj 0;{idx};,;{struc}\n'
        return data