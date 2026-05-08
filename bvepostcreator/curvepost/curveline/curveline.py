from curvepost.metro.metro_processor import CityLineProcess
from curvepost.spiral_processor import SpiralProcessor
from curvepost.train.train_processor import TrainProcessor
from infrastructure.csvmanager import CSVManager
import os

class CurveLineProcessor:
    def __init__(self, source_directory, work_directory, al_type, log):
        self.source_directory = source_directory
        self.work_directory = work_directory
        self.al_type = al_type
        self.log = log

    def process_cityline(self, ip, curvetype, img_f_name, openfile_name, structure, speed):
        tcl = 'TCL=' + str(int(ip.PC_STA - ip.SP_STA)) if ip.curvetype == '완화곡선' else 0
        citylineprocess = CityLineProcess(curvetype, ip.radius, ip.cant, tcl,
                                          img_f_name, self.source_directory, self.work_directory)
        citylineprocess.process()
        output_file = CurveOutputService.copy_and_export(self.source_directory, self.work_directory,
                                                         openfile_name, img_f_name, curvetype, ip.radius)
        if speed < 120 and curvetype in ['BC', 'PC']:

            add_file = os.path.join(self.source_directory, f'속도제한표-{structure}용.csv')
            CSVManager.insert_other_text(output_file, add_file)
        return output_file

    def process_trainline(self, ip, curvetype, station_text, img_f_name, openfile_name, structure):
        trainprocessor = TrainProcessor(self.source_directory, self.work_directory)
        trainprocessor.process(curvetype, station_text, str(ip.cant), img_f_name)
        if curvetype in ['SP', 'PS', 'BC', 'EC']:
            spiral_processor = SpiralProcessor(self.source_directory, self.work_directory)
            spiral_processor.process(ip.radius, img_f_name, structure)
        return CurveOutputService.copy_and_export(self.source_directory, self.work_directory,
                                                  openfile_name, img_f_name, curvetype, ip.radius)
