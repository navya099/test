import os
import re

class CurvePreprocessor:
    @staticmethod
    def get_builder(path):
        flag = CurvePreprocessor.define_flag_from_read_file(path)
        if flag == 'BVE':
            return BVEVIPDATABuilder()
        elif flag == 'CIVIL3D':
            return C3DVIPDATABuilder()
        else:
            raise ValueError(f"지원하지 않는 flag: {flag}")


    @staticmethod
    def define_flag_from_read_file(pitch_info_path):
        flag = None
        try:
            file_path = pitch_info_path
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".txt":
                flag = 'BVE'
            elif ext == ".xlsx":
                flag = 'CIVIL3D'
            else:
                raise ValueError('지원하지 않는 FLAG')
            return flag
        except Exception as e:
            raise e

    @staticmethod
    def remove_duplicate_radius(data):
        filtered_data = []
        previous_radius = None

        for row in data:
            try:
                station, radius, cant = map(float, row)
                station = int(station)
            except ValueError:
                print(f"잘못된 데이터 형식: {row}")
                continue

            if radius != previous_radius:
                filtered_data.append((station, radius, cant))
                previous_radius = radius

        return filtered_data

    @staticmethod
    def process_sections(data):
        sections = []
        current_section = []

        for row in data:
            try:
                station, radius, cant = map(float, row)
                station = int(station)
            except ValueError:
                print(f"잘못된 데이터 형식: {row}")
                continue

            current_section.append((station, radius, cant))

            if radius == 0.0 and current_section:
                sections.append(current_section)
                current_section = []

        return sections

    @staticmethod
    def convert_pitch_lines(lines):
        """
        .pitch 제거 → ; 를 ,로 변환 → 마지막 , 제거
        lines가 List[List[str]] 혹은 List[str]인 경우 모두 처리 가능
        """
        converted = []

        for line in lines:
            # line이 리스트이면 문자열로 결합
            if isinstance(line, list):
                line = ','.join(line)

            line = line.strip()

            # 1단계: ".CURVE" 등 대소문자 구분 없이 제거 (정규식 사용)
            line = re.sub(r'\.pitch', '', line, flags=re.IGNORECASE)

            # 4단계: line의 각 요소 추출
            parts = line.split(',')
            if len(parts) == 1 or len(parts) == 0:
                print(f"[경고] 잘못된 행 형식: {line} → 건너뜀")
                continue  # 또는 raise ValueError(f"Invalid line format: {line}")
            try:
                if len(parts) == 2:
                    sta, pitch = map(float, parts)
                    pitch *= 0.001  # 내부 단위 자료구조 통일을 위해 0.001곱하기
                else:
                    raise ValueError

                converted.append((sta, pitch))

            except ValueError:
                print(f"[오류] 숫자 변환 실패: {line} → 건너뜀")
                continue

        return converted