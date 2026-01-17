from Structure.structure import Structure
from Structure.structurecollection import StructureCollection
from core.bve.bve_block_exporter import BVEBlcokExporter
from core.bve.bve_info_saver import BVEInfoSaver
from core.bve.structure_saver import StructureSaver
from core.bve.terrain_generator import TerrainGerator
import numpy as np

class BVEProcess:
    def __init__(self, results: dict):
        self.results = results
    def run(self):
        #top10에서 curve추출
        segments = self.results['plan_full']['segments']
        length = self.results['plan_full']['linestring'].length
        pitchs = self.results['profile']['fg_profile']
        curve_blocks = BVEBlcokExporter.export_curve_info(segments, start_sta=0.0,end_sta=length)
        pitch_blocks = BVEBlcokExporter.export_pitch_info(pitchs, start_sta=0.0,end_sta=length)
        #1 curve_info txt저장
        BVEInfoSaver.save_curve_info('C:/Temp/curve_info.txt', curve_blocks)
        #2 pitch_info txt 저장
        BVEInfoSaver.save_pitch_info('C:/Temp/pitch_info.txt', pitch_blocks)
        #3 height info txt 저장
        design_elevs =  self.results['profile']['design_elevs']
        ground_elevs = self.results['profile']['ground_elevs']

        elevdiff_list = np.array(ground_elevs) - np.array(design_elevs)

        height_blocks = TerrainGerator.create_terrain(elevdiff_list)
        BVEInfoSaver.save_height_info('C:/Temp/height_info.txt', height_blocks)

        #4 bve_cooridnates 저장
        coords = self.results['plan_full']['tmcoords']
        BVEInfoSaver.save_cooridnate_info('C:/Temp/bve_coordinates.txt', coords)

        #5 구조물xlsx 저장
        bridges = self.results['result']['bridges']
        turnnels  = self.results['result']['turnnels']
        structures = StructureCollection()
        structures.append(bridges)
        structures.append(turnnels)
        StructureSaver.save_to_excel(structures, 'C:/Temp/구조물.xlsx')
