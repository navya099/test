import fitz
import os

class TrainOutputManager:
    """출력 담당 매니저"""
    @staticmethod
    def export_png(doc, filename: str, work_directory: str):
        page = doc[0]
        pix = page.get_pixmap()
        orig_width, orig_height = pix.width, pix.height

        target_width, target_height = 300, 200
        scale = min(target_width / orig_width, target_height / orig_height)

        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))

        save_file = os.path.join(work_directory, filename + '.png')
        pix.save(save_file)
