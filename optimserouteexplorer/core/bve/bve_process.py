from Structure.structurecollection import StructureCollection
import numpy as np
import os
from core.bve.base_text import create_base_txt
from core.bve.bve_block_exporter import BVEBlcokExporter
from core.bve.bve_info_saver import BVEInfoSaver
from core.bve.height_syntax_maker import TerrainSyntaxMaker
from core.bve.structure_saver import StructureSaver
from core.bve.structure_syntax_maker import BVEStructureSyntaxMaker
from core.bve.terrain_generator import TerrainGerator
from core.util import Vector3
from out.bve_export import BVEExporter


class BVEProcess:
    def __init__(self, results: dict):
        self.results = results

    def run(self):
        print('-----INFO파일 저장중-----')
        self.save_infos()
        print('-----INFO파일 저장완료-----')
        print('-----BVE구문파일 저장중-----')
        self.create_bve_syntax()
        print('-----BVE구문파일 저장완료-----')
        print('-----모든 작업 완료-----')

    def get_structures(self) -> StructureCollection:
        bridges = self.results['result']['bridges']
        tunnels = self.results['result']['tunnels']
        structures = StructureCollection()
        structures.extend(bridges)
        structures.extend(tunnels)
        return structures

    def get_elevations(self):
        design_elevs = self.results['profile']['design_elevs']
        ground_elevs = self.results['profile']['ground_elevs']

        elevdiff_list = np.array(design_elevs) - np.array(ground_elevs)
        return design_elevs, ground_elevs, elevdiff_list

    def save_infos(self):
        segments = self.results['plan_full']['segments']
        length = self.results['plan_full']['linestring'].length
        fg_profile = self.results['profile']['fg_profile']
        slopes = self.results['profile']['slopes']
        pitchs = [(sta, slope) for (sta, elevation), slope in zip(fg_profile, slopes)]



        curve_blocks = BVEBlcokExporter.export_curve_info(segments, 0.0, length)
        pitch_blocks = BVEBlcokExporter.export_pitch_info(pitchs, 0.0, length)

        BVEInfoSaver.save_curve_info('C:/Temp/curve_info.txt', curve_blocks)
        BVEInfoSaver.save_pitch_info('C:/Temp/pitch_info.txt', pitch_blocks)

        design_elevs, ground_elevs, elevdiff_list = self.get_elevations()
        height_blocks = TerrainGerator.create_terrain(elevdiff_list)
        BVEInfoSaver.save_height_info('C:/Temp/height_info.txt', height_blocks)

        coords = self.results['plan_full']['tmcoords']

        vec_list = [Vector3(x=c[0], y=c[1], z=0.0) for c in coords]
        BVEInfoSaver.save_cooridnate_info('C:/Temp/bve_coordinates.txt', vec_list)

        structures = self.get_structures()
        StructureSaver.save_to_excel(structures, 'C:/Temp/구조물.xlsx')

    def create_bve_syntax(self):
        plan_full = self.results['plan_full']
        BVEExporter.export_plan('D:/BVE/루트/Railway/Route/연습용루트/평면선형.txt', plan_full)

        profile = self.results['profile']
        BVEExporter.export_profile('D:/BVE/루트/Railway/Route/연습용루트/종단선형.txt', profile)

        structures = self.get_structures()
        structure_text = BVEStructureSyntaxMaker.create_structure_syntax(structures)
        BVEExporter.export('D:/BVE/루트/Railway/Route/연습용루트/구조물.txt', structure_text)

        design_elevs, ground_elevs, elevdiff_list = self.get_elevations()
        height_blocks = TerrainGerator.create_terrain(elevdiff_list)
        terrain_text = TerrainSyntaxMaker.run(elevdiff_list)
        BVEExporter.export_terrain('D:/BVE/루트/Railway/Route/연습용루트/', terrain_text)

        base = create_base_txt()
        base.insert(2, f'.elevation {design_elevs[0]}')

        length = self.results['plan_full']['linestring'].length
        base.append(f'{length},.sta END POINT;')
        base.append(f'{length + 100},.STOP 0;')

        csv_path = os.path.join('D:/BVE/루트/Railway/Route/연습용루트/', "테스트.csv")
        BVEExporter.export(csv_path, base)