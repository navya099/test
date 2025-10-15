import numpy as np

from Structure.bridge import Bridge
from Structure.structurecollection import StructureCollection
from Structure.tunnel import Tunnel


class StructureDetector:
    """
    설계고-지반고(dz)와 구간거리(ds)를 기반으로
    교량과 터널 구간을 탐지하는 클래스
    """
    def __init__(self, height_threshold=15, length_threshold=100):
        self.height_threshold = height_threshold  # 최소 높이
        self.length_threshold = length_threshold  # 최소 길이

    def detect(self, dz: np.ndarray, ds: np.ndarray, chain) -> tuple[StructureCollection, StructureCollection]:
        """
        교량/터널 판정
        Returns:
            tuple[StructureCollection, StructureCollection]
        """
        bridges = StructureCollection()
        tunnels = StructureCollection()
        bridge_counter = 1
        tunnel_counter = 1

        start_idx = 0
        while start_idx < len(dz) - 1:
            current_sign = np.sign(dz[start_idx])
            end_idx = start_idx

            while end_idx < len(dz) - 1 and np.sign(dz[end_idx]) == current_sign:
                end_idx += 1
            segment_len = ds[start_idx:end_idx].sum()
            segment_height = np.max(np.abs(dz[start_idx:end_idx]))

            #교량생성
            if current_sign > 0 and segment_height >= 15 and segment_len >= 100:
                bridges.append(Bridge(f'B{bridge_counter}', start_idx * chain, end_idx * chain))
                bridge_counter += 1
            #터널생성
            elif current_sign < 0 and segment_height >= 15 and segment_len >= 100:
                tunnels.append(Tunnel(f'T{tunnel_counter}', start_idx * chain, end_idx * chain))
                tunnel_counter += 1

            start_idx = end_idx

        return bridges, tunnels
