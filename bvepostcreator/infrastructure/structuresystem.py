import pandas as pd

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
        """xlsx 파일을 읽고 교량과 터널 정보를 반환하는 메서드"""
        self.structure_list = {'bridge': [], 'tunnel': []}

        # xlsx 파일 읽기

        df_bridge = pd.read_excel(self.filepath, sheet_name='교량', header=None)
        df_tunnel = pd.read_excel(self.filepath, sheet_name='터널', header=None)

        # 첫 번째 행을 열 제목으로 설정
        df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
        df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

        # 교량 구간과 터널 구간 정보
        for _, row in df_bridge.iterrows():
            self.structure_list['bridge'].append((row['br_START_STA'], row['br_END_STA']))

        for _, row in df_tunnel.iterrows():
            self.structure_list['tunnel'].append((row['tn_START_STA'], row['tn_END_STA']))

    @staticmethod
    def define_bridge_tunnel_at_station(sta, structure_list):
        """sta가 교량/터널/토공 구간에 해당하는지 구분하는 메서드"""
        for start, end in structure_list['bridge']:
            if start <= sta <= end:
                return '교량'

        for start, end in structure_list['tunnel']:
            if start <= sta <= end:
                return '터널'

        return '토공'

    def apply_brokenchain_to_structure(self, brokenchain):
        """
        structure_list의 각 구간(start, end)에 brokenchain 값을 더해서
        같은 구조로 반환하는 메서드.
        :param brokenchain: float, 오프셋 값 (예: 0.0 또는 양수/음수)
        """
        if brokenchain == 0.0:
            # 오프셋이 없으면 원본 그대로 반환
            return

        updated_structure = {'bridge': [], 'tunnel': []}

        for key in ['bridge', 'tunnel']:
            for start, end in self.structure_list.get(key, []):
                new_start = start + brokenchain
                new_end = end + brokenchain
                updated_structure[key].append((new_start, new_end))

        self.structure_list = updated_structure