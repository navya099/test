from common.common_utils import format_distance
from curvepost.curve_data_filter import CurveDataFilter
from curvepost.curve_util import cal_speed
from curvepost.curveline.curveline import CurveLineProcessor
from curvepost.curveline.object_facotry import CurveObjectFactory


class CurveProcessor:
    def __init__(self, source_directory, work_directory, target_directory, al_type, offset, start_idx, log):
        self.source_directory = source_directory
        self.work_directory = work_directory
        self.target_directory = target_directory
        self.al_type = al_type
        self.offset = offset
        self.start_idx = start_idx
        self.log = log

        self.filter = CurveDataFilter(log)
        self.processor = CurveLineProcessor(source_directory, work_directory, al_type, log)
        self.factory = CurveObjectFactory(offset)

    def build(self, start, end, ipdatas, structure_processor):
        object_index = self.start_idx
        objects = []
        object_folder = self.target_directory.split("Object/")[-1]

        valid_ips = self.filter.filter(ipdatas, start, end)
        for i, (ip, lines) in enumerate(valid_ips):
            for curvetype, station in lines:
                structure = structure_processor.define_bridge_tunnel_at_station(station)
                station_text = format_distance(station)
                img_f_name = f'IP{i+1}_{curvetype}'
                openfile_name = f'{curvetype}_{structure}용'
                speed = int(cal_speed(ip.radius))

                self.processor.process(ip, curvetype, station_text, img_f_name, openfile_name, structure, speed)

                csvobject = self.factory.create(ip, curvetype, structure, station, object_index,
                                                img_f_name, object_folder, speed)
                objects.append(csvobject)
                object_index += 1
        return objects
