from core.bve.commnd_genmerator import BVECommandGenerator


class TerrainSyntaxMaker:
    @staticmethod
    def run(elevlist) -> list:
        out = []
        for i, elev in enumerate(elevlist):
            pos = i * 25
            height = TerrainSyntaxMaker.create_height(pos, elev)
            ground = TerrainSyntaxMaker.create_ground(pos, elev)
            nori = TerrainSyntaxMaker.create_nori(pos, elev, slope=1.5)
            out.append([height, ground, nori])
        return out

    @staticmethod
    def create_ground(pos, elev):
        return BVECommandGenerator.make_command(pos, 'ground',0 if elev > 1 else 3)
    @staticmethod
    def create_height(pos, elev):
        return  BVECommandGenerator.make_command(pos, 'height', elev)

    @staticmethod
    def create_nori(pos, elev, slope):
        x = elev * slope
        rail1 = BVECommandGenerator.make_command(pos, 'rail',200, -x, -elev, 88)
        rail2 = BVECommandGenerator.make_command(pos,'rail' ,201, x, -elev, 87)
        return rail1, rail2