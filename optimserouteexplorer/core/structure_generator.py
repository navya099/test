from Structure.bridge import Bridge
from Structure.structurecollection import StructureCollection
from Structure.tunnel import Tunnel


class StructureGenerator:
    def __init__(self) -> None:
        self.structures: StructureCollection = StructureCollection()

    def _group_elevations(self, sta_list, elevlist, threshold, min_length, tunnel=False, extra_cond=None):
        groups = []
        current_group = []
        consecutive = 0

        for i, elev in enumerate(elevlist):
            if (not tunnel and elev >= threshold) or (tunnel and elev <= threshold):
                current_group.append(sta_list[i])
                consecutive += 1
                # 그룹 종료 조건
                if i == len(elevlist) - 1 or \
                   (not tunnel and elevlist[i+1] < threshold) or \
                   (tunnel and elevlist[i+1] > threshold):
                    if consecutive >= min_length:
                        if not tunnel or (extra_cond and extra_cond(elevlist, current_group, i)):
                            groups.append((current_group[0], current_group[-1]))
                    current_group = []
                    consecutive = 0
        return groups

    def define_structure(self, sta_list, elevlist,
                         bridge_threshold=12, tunnel_threshold=-12,
                         min_length=6, tunnel_min=-40):
        # 교량 판정
        bridge_groups = self._group_elevations(sta_list, elevlist,
                                               threshold=bridge_threshold,
                                               min_length=min_length,
                                               tunnel=False)

        # 터널 판정 (추가 조건: 최소 -40 이하)
        tunnel_groups = self._group_elevations(sta_list, elevlist,
                                               threshold=tunnel_threshold,
                                               min_length=min_length,
                                               tunnel=True,
                                               extra_cond=lambda elevlist, group, i:
                                                   min(elevlist[i-len(group)+1:i+1]) <= tunnel_min)

        # 객체 생성
        for i, (start, end) in enumerate(tunnel_groups, 1):
            self.structures.append(Tunnel(f'Tunnel_{i}', start, end))
        for i, (start, end) in enumerate(bridge_groups, 1):
            self.structures.append(Bridge(f'Bridge_{i}', start, end))

        # 카운트는 StructureCollection에서 관리하도록 위임