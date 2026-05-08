from curvepost.curveline.ouputservice import CurveOutputService
from curvepost.spiral_processor import SpiralProcessor
from curvepost.train.post_data import TrainPostData
from curvepost.train.train_processor import TrainProcessor


class TrainLineProcessorWrapper:
    def __init__(self, source_directory, work_directory):
        self.source_directory = source_directory
        self.work_directory = work_directory

    def process(self, ip, curvetype, station_text, img_f_name, openfile_name, structure):
        trainprocessor = TrainProcessor(self.source_directory, self.work_directory)
        tpd = TrainPostData(curvetype=curvetype, station=station_text, cant='0', filename=img_f_name)
        trainprocessor.process(tpd)
        if curvetype in ['SP', 'PS', 'BC', 'EC']:
            spiral_processor = SpiralProcessor(self.source_directory, self.work_directory)
            spiral_processor.process(ip.radius, img_f_name, structure)
        return CurveOutputService.copy_and_export(self.source_directory, self.work_directory,
                                                  openfile_name, img_f_name, curvetype, ip.radius)
