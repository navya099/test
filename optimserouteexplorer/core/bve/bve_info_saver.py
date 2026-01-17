from core.bve.curveblock import Curveblock
from core.bve.heightblock import HeightBlock
from core.bve.pitchblock import PitchBlock
from core.util import Vector3


class BVEInfoSaver:
    @staticmethod
    def save_info(filepath, blocks, formatter):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for block in blocks:
                    f.write(formatter(block) + "\n")
            print(f"[정보] 데이터가 '{filepath}'에 저장되었습니다.")
        except Exception as e:
            print(f"[오류] 파일 저장 실패: {e}")

    @staticmethod
    def save_curve_info(filepath, blocks: list[Curveblock]):
        BVEInfoSaver.save_info(filepath, blocks, lambda b: f"{b.sta},{b.radius},{b.cant}")

    @staticmethod
    def save_pitch_info(filepath, blocks: list[PitchBlock]):
        BVEInfoSaver.save_info(filepath, blocks, lambda b: f"{b.sta},{b.pitch}")

    @staticmethod
    def save_height_info(filepath, blocks: list[HeightBlock]):
        BVEInfoSaver.save_info(filepath, blocks, lambda b: f"{b.sta},{b.height}")

    @staticmethod
    def save_cooridnate_info(filepath, blocks: list[Vector3]):
        BVEInfoSaver.save_info(filepath, blocks, lambda b: f"{b.x},{b.y},{b.z}")