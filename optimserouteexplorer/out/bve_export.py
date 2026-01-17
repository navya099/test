class BVEExporter:
    def __init__(self):
        pass
    def export(self, filepath, data):
        bc = data['bc_stas']
        ec = data['ec_stas']
        r = data['radius']

        with open(filepath, 'w') as f:
            for b,e,r in zip(bc, ec, r):
                f.write(f'{b:.2f},.curve {r};0;\n')
                f.write(f'{e:.2f},.curve 0;0;\n')
    def export_profile(self ,filepath, data):
        fg = data['fls'] #리스트
        stations = [s for s, _ in fg]

        pitch = data['slopes']
        with open(filepath, 'w') as f:
            for s,p in zip(stations, pitch):
                f.write(f'{s},.pitch {p * 1000:.2f};\n')