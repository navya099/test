from infrastructure.structuresystem import StructureProcessor
from kmpost.typeresolver import KMPostTypeResolver

class KMObjectBuilder:
    """KM포스트 빌더"""
    def __init__(self, start_block, last_block, structure_list, alignmenttype, offset, interval):
        self.start_block = start_block
        self.last_block = last_block
        self.structure_list = structure_list
        self.alignmenttype = alignmenttype
        self.offset = offset
        self.interval = interval

    def run(self):
        result = []

        for i in range(
            int(self.start_block // self.interval),
            int(self.last_block // self.interval)
        ):
            sta = i * self.interval
            structure = StructureProcessor.define_bridge_tunnel_at_station(
                sta, self.structure_list
            )
            post_type = KMPostTypeResolver.resolve(sta, interval=self.interval)

            if not post_type:
                continue
            result.append([sta, post_type, structure])

        return result