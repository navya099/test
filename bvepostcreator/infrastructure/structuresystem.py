import pandas as pd

from common.stationmanager import StationManager
from model.stationdata import StationData


class StructureProcessor:
    """구조물처리 프로세서"""

    def __init__(self, filepath):
        self.structure_list = {}
        self.filepath = filepath

    def process_structure(self, brokenchain):
        self.find_structure_section()
        # 구조물 측점 파정처리
        self.apply_brokenchain_to_structure(brokenchain)

    def find_structure_section(self):
        """xlsx 파일 읽고 교량과 터널 정보를 StationData로 반환"""
        self.structure_list = {'bridge': [], 'tunnel': []}

        df_bridge = pd.read_excel(self.filepath, sheet_name='교량', header=None)
        df_tunnel = pd.read_excel(self.filepath, sheet_name='터널', header=None)

        if not df_bridge.empty and df_bridge.shape[1] >= 4:
            df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
            for _, row in df_bridge.iterrows():
                start = StationData(origin_sta=row['br_START_STA'])
                end = StationData(origin_sta=row['br_END_STA'])
                self.structure_list['bridge'].append((start, end))

        if not df_tunnel.empty and df_tunnel.shape[1] >= 4:
            df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']
            for _, row in df_tunnel.iterrows():
                start = StationData(origin_sta=row['tn_START_STA'])
                end = StationData(origin_sta=row['tn_END_STA'])
                self.structure_list['tunnel'].append((start, end))

    def define_bridge_tunnel_at_station(self, sta):
        """sta가 교량/터널/토공 구간에 해당하는지 구분하는 메서드"""
        for start, end in self.structure_list['bridge']:
            if start.after_sta <= sta <= end.after_sta:
                return '교량'

        for start, end in self.structure_list['tunnel']:
            if start.after_sta <= sta <= end.after_sta:
                return '터널'

        return '토공'

    def apply_brokenchain_to_structure(self, brokenchain):
        """
        structure_list의 각 구간(start, end)에 brokenchain 값을 더해서
        같은 구조로 반환하는 메서드.
        :param brokenchain: float, 오프셋 값 (예: 0.0 또는 양수/음수)
        """
        if brokenchain == 0.0:
            return  # 오프셋이 없으면 그대로

        for key in ['bridge', 'tunnel']:
            for start_sd, end_sd in self.structure_list.get(key, []):
                start_sd.after_sta = start_sd.origin_sta + brokenchain
                end_sd.after_sta = end_sd.origin_sta + brokenchain

    def apply_after_station_to_structure(self, reverse_start, last_block):
        """
        structure_list의 각 구간에 역측점 적용
        """
        for key in ['bridge', 'tunnel']:
            for start_sd, end_sd in self.structure_list.get(key, []):
                start_sd.after_sta = StationManager.to_reverse_station(last_block, reverse_start, start_sd.origin_sta)
                end_sd.after_sta = StationManager.to_reverse_station(last_block, reverse_start, end_sd.origin_sta)

    def reverse(self):
        """구간 시작/끝 뒤집기"""
        for key in ['bridge', 'tunnel']:
            reversed_list = []
            for start_sd, end_sd in self.structure_list.get(key, []):
                reversed_list.append((end_sd, start_sd))
            self.structure_list[key] = reversed_list
