# core/system_impl/output_systems.py
import abc
import csv
import math
from core.system.system import System
from core.constants import ComponentKey


class BaseOutputSystem(System):
    """출력 시스템의 추상 베이스 클래스"""
    requires_components = frozenset({ComponentKey.TURNOUT_SPEC, ComponentKey.BRANCH_COORDS})

    @abc.abstractmethod
    def execute(self, entities, components):
        pass

    def _format_summary(self, spec) -> str:
        return (
            f"=== 건넘선 설계 결과 ===\n"
            f"곡선장(cl): {spec.start_length:.1f} m\n"
            f"직선장(sl): {spec.middle_length:.1f} m\n"
            f"반지름(R): {spec.radius:.2f} m\n"
            f"접선각(θ): {math.degrees(spec.cross_angle):.3f}°\n"
        )


# -------------------------------------------------------------------------
# 1. 콘솔 출력 시스템
# -------------------------------------------------------------------------
class ConsoleOutputSystem(BaseOutputSystem):
    def execute(self, entities, components):
        spec = components[ComponentKey.TURNOUT_SPEC]
        coords_data = components[ComponentKey.BRANCH_COORDS]

        # 설계 요약 출력
        print("\n" + self._format_summary(spec))

        # 좌표 미리보기 출력
        print("--- 분기 경로 좌표 (상위 5개) ---")
        for i, p in enumerate(coords_data["points"][:5]):
            print(f"P{i}: X={p[0]:.3f}, Y={p[1]:.3f}")
        print(f"... (총 {len(coords_data['points'])}개)\n")


# -------------------------------------------------------------------------
# 2. TXT 파일 출력 시스템
# -------------------------------------------------------------------------
class TxtOutputSystem(BaseOutputSystem):
    def execute(self, entities, components):
        spec = components[ComponentKey.TURNOUT_SPEC]
        coords_data = components[ComponentKey.BRANCH_COORDS]
        config = components[ComponentKey.OUTPUT_CONFIG]

        file_path = config.file_path or "output_result.txt"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self._format_summary(spec))
            f.write("\n--- 전체 좌표 ---\n")
            for i, p in enumerate(coords_data["points"]):
                f.write(f"{i},{p[0]:.4f},{p[1]:.4f}\n")

        self.logger.info(f"TXT 파일 저장 완료: {file_path}")


# -------------------------------------------------------------------------
# 3. CSV 파일 출력 시스템
# -------------------------------------------------------------------------
class CsvOutputSystem(BaseOutputSystem):
    def execute(self, entities, components):
        spec = components[ComponentKey.TURNOUT_SPEC]
        coords_data = components[ComponentKey.BRANCH_COORDS]
        config = components[ComponentKey.OUTPUT_CONFIG]

        file_path = config.file_path or "output_coords.csv"

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 헤더 작성
            writer.writerow(["Index", "X", "Y"])
            # 데이터 작성
            for i, p in enumerate(coords_data["points"]):
                writer.writerow([i, f"{p[0]:.4f}", f"{p[1]:.4f}"])

        self.logger.info(f"CSV 파일 저장 완료: {file_path}")
        # 콘솔에도 요약은 보여줌
        print(f"\n[알림] CSV 저장 완료: {file_path}")
        #print(self._format_summary(spec))