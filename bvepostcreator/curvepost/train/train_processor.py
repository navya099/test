import fitz
import os

from curvepost.train.post_data import TrainPostData
from curvepost.train.text_layout_service import TextLayoutService


class TrainProcessor:
    """일반철도, 준고속철도, 고속철도용"""
    def __init__(self, source_directory: str, work_directory: str):
        self.source_directory = source_directory
        self.work_directory = work_directory

    def process(self, post_data: TrainPostData):
        ai_file = os.path.join(self.source_directory, post_data.curvetype + '.AI')
        doc = fitz.open(ai_file)

        x_pt, y_pt = TextLayoutService.calculate_position(post_data.station, post_data.curvetype)

        for page in doc:
            page.insert_text((x_pt, y_pt), post_data.station,
                             fontname="helvetica", fontsize=160.15, color=(1,1,1))

        return doc  # 저장은 OutputManager에서 담당
