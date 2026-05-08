from curvepost.metro.wrapper import CityLineProcessorWrapper
from curvepost.train.wrapper import TrainLineProcessorWrapper


class CurveLineProcessor:
    def __init__(self, source_directory, work_directory, al_type, log):
        self.al_type = al_type
        self.log = log
        self.cityline = CityLineProcessorWrapper(source_directory, work_directory)
        self.trainline = TrainLineProcessorWrapper(source_directory, work_directory)

    def process(self, ip, curvetype, station_text, img_f_name, openfile_name, structure, speed):
        if self.al_type == '도시철도':
            return self.cityline.process(ip, curvetype, img_f_name, openfile_name, structure, speed)
        else:
            return self.trainline.process(ip, curvetype, station_text, img_f_name, openfile_name, structure)
