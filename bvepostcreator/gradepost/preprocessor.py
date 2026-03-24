import os
from common.file_io import try_read_file

class VIPPreprocessor:
    @staticmethod
    def preprocsee_read_file(pitch_info_path, brokenchain):
        flag = None
        data = None
        try:
            file_path = pitch_info_path
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".txt":
                data = try_read_file(file_path)  # TXT 읽기 시도
                flag = 'BVE'
            elif ext == ".xlsx":
                data = parse_ptich_excel(file_path, brokenchain)  # xlsx읽기 시도
                flag = 'CIVIL3D'
            else:
                raise ValueError('지원하지 않는 FLAG')

        except Exception as e:
            raise e

    @staticmethod
    def remove_duplicate_pitch(data):
        """중복된 데이터 제거"""
        filtered_data = []
        previous_pitch = None

        for row in data:
            try:
                station, pitch = map(float, row)
            except ValueError:
                print(f"잘못된 데이터 형식: {row}")
                continue

            if pitch != previous_pitch:
                filtered_data.append((station, pitch))
                previous_pitch = pitch

        return filtered_data

    @staticmethod
    def create_sections(data, threshold=75.0, min_points=1):
        """pitch_info에서 구간 분리"""
        sections = []
        current_section = []
        prev_station = None

        for row in data:
            try:
                station, pitch = map(float, row)
            except (ValueError, TypeError):
                continue

            if prev_station is not None:
                gap = station - prev_station
                if gap >= threshold:
                    if len(current_section) >= min_points:
                        sections.append(current_section)
                    current_section = []

            current_section.append((station, pitch))
            prev_station = station

        if current_section and len(current_section) >= min_points:
            sections.append(current_section)

        return sections