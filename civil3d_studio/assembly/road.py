from typing import List

from subassembly.link import SubassemblyLink


class RoadAssembly:
    """좌측(Left) 및 우측(Right) 서브어셈블리 체인으로 구성된 도로 표준횡단(Assembly)"""
    def __init__(self, name: str, left_links: List[SubassemblyLink], right_links: List[SubassemblyLink]):
        self.name = name
        self.left_links = left_links
        self.right_links = right_links