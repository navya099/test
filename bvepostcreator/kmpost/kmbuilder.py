from common.stationmanager import StationManager
from infrastructure.structuresystem import StructureProcessor
from kmpost.typeresolver import KMPostTypeResolver
from model.stationdata import StationData


class KMObjectBuilder:
    """KM포스트 빌더"""
    def __init__(self, start_block, last_block, structure_processor, alignmenttype, offset, interval, reverse_start ,is_reverse):
        self.start_block = start_block
        self.last_block = last_block
        self.structure_processor = structure_processor
        self.alignmenttype = alignmenttype
        self.offset = offset
        self.interval = interval
        self.reverse_start = reverse_start
        self.is_reverse = is_reverse

    def run(self):
        result = []

        if self.is_reverse:#역방향
            #구조물 측점 역방향을 after에 적용
            self.structure_processor.apply_after_station_to_structure(self.reverse_start, self.last_block)
            # 구조물 측점 시작 끝은 역방향에서는 반대임 뒤짒기
            self.structure_processor.reverse()
            #시작 끝은 방향이 반대임으로 뒤집어야함
            end_block = StationManager.to_reverse_station(self.last_block, self.reverse_start, self.start_block)
            start_block = StationManager.to_reverse_station(self.last_block, self.reverse_start, self.last_block)

        else:#정방향은 그대로
            start_block = self.start_block
            end_block = self.last_block

        for i in range(int(start_block // self.interval), int(end_block // self.interval)):
            sta = i * self.interval
            stadata = self.create_station_data(sta)
            structure, post_type = self.get_structure_and_post_type(stadata.after_sta)
            if not post_type:
                continue
            result.append([stadata, post_type, structure])

        return result

    def create_station_data(self, sta):
        if self.is_reverse:
            forward_sta = StationManager.to_reverse_station(self.last_block, self.reverse_start, sta)
            return StationData(origin_sta=forward_sta, after_sta=sta)
        return StationData(origin_sta=sta)

    def get_structure_and_post_type(self, sta):
        structure = self.structure_processor.define_bridge_tunnel_at_station(sta)
        post_type = KMPostTypeResolver.resolve(sta, interval=self.interval)
        return structure, post_type
