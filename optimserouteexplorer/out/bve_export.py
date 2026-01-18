import os

class BVEExporter:
    @staticmethod
    def export_plan(filepath, data):
        bc = data['bc_stations']
        ec = data['ec_stations']
        r = data['radius_list']

        with open(filepath, 'w') as f:
            for b,e,r in zip(bc, ec, r):
                f.write(f'{b:.2f},.curve {r};0;\n')
                f.write(f'{e:.2f},.curve 0;0;\n')
    @staticmethod
    def export_profile(filepath, data):
        fg = data['fg_profile'] #리스트
        stations = [s for s, _ in fg]

        pitch = data['slopes']
        with open(filepath, 'w') as f:
            for s,p in zip(stations, pitch):
                f.write(f'{s},.pitch {p * 1000:.2f};\n')

    @staticmethod
    def export(filepath, data):
        with open(filepath, 'w', encoding='utf-8') as f:
            if isinstance(data, (list, tuple)):
                for item in data:
                    f.write(str(item) + "\n")
            else:
                f.write(str(data))

    @staticmethod
    def export_terrain(folder, data):
        height_path = os.path.join(folder, 'height.txt')
        ground_path = os.path.join(folder, 'ground.txt')
        nori_path = os.path.join(folder, '사면.txt')

        #데이터 분리
        heights = [h for h, _, _ in data]
        grounds = [g for _, g, _ in data]
        noris = [n for _, _, n in data]
        BVEExporter.export(height_path, heights)
        BVEExporter.export(ground_path, grounds)
        BVEExporter.export_nori(nori_path, noris)

    @staticmethod
    def export_nori(filepath, data):

        with open(filepath, 'w') as f:
            f.write(',;좌측사면\n')
            for l,_ in data:
                f.write(f'{l}\n')
            f.write(',;우측사면\n')
            for _, r in data:
                f.write(f'{r}\n')