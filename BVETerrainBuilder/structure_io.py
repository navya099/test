import pandas as pd
import logging

class StructureLoader:
    def load(self, structurefilepath):
        logging.debug("구조물 파일 읽기")
        return self.parse_structure(structurefilepath)

    def parse_structure(self, filepath):
        structure_list = {'bridge': [], 'tunnel': []}


        df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
        df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

        df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
        df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

        for _, row in df_bridge.iterrows():
            structure_list['bridge'].append((row['br_NAME'], row['br_START_STA'], row['br_END_STA']))
        for _, row in df_tunnel.iterrows():
            structure_list['tunnel'].append((row['tn_NAME'], row['tn_START_STA'], row['tn_END_STA']))
        return structure_list