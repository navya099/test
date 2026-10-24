from openpyxl.workbook import Workbook

from xref.Structure.bridge import Bridge
from xref.Structure.structurecollection import StructureCollection
from xref.Structure.tunnel import Tunnel


class StructureSaver:
    @staticmethod
    def save_to_excel(structures: StructureCollection, output_path):

        wb = Workbook()

        # 시트: 교량
        bridge_ws = wb.active
        bridge_ws.title = '교량'
        #bridge_ws.append(['교량명', '시점', '종점', '연장'])

        # 시트: 터널
        tunnel_ws = wb.create_sheet(title='터널')
        #tunnel_ws.append(['터널명', '시점', '종점', '연장'])

        for structure in structures:
            name = structure.name
            start = structure.startsta
            end = structure.endsta
            length = end - start
            row = [name, start, end, length]

            if isinstance(structure, Bridge):
                bridge_ws.append(row)
            elif isinstance(structure, Tunnel):
                tunnel_ws.append(row)

        wb.save(output_path)
        print(f"구조물 정보가 Excel 파일로 저장되었습니다: {output_path}")