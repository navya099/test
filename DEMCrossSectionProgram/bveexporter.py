import os

import numpy as np


class BVEExporter:
    """BVE 구문 익스포터 (OpenBVE 노선 뼈대 스크립트 일괄 생성 자동화)"""

    @staticmethod
    def initialize_files(save_folder):
        """출력 파일이 기존에 존재한다면 초기화(삭제)"""
        files = ['사면좌.txt', '사면우.txt', 'height.txt', 'ground.txt']
        for filename in files:
            filepath = os.path.join(save_folder, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

    @staticmethod
    def export_all_sections(save_folder, all_section_results, track_type="단선", track_distance=4.0, track_width=8.0):
        """
        하이브리드 캐시에 수집된 전구간 단면 데이터를 받아
        BVE 표준 노선 구문 파일 4종을 단 1초 만에 메모리 덤프 방식으로 생성합니다.

        :param save_folder: 텍스트 파일이 저장될 폴더 경로
        :param all_section_results: Run.cache_data에 누적된 {idx: section_data_dict} 딕셔너리 또는 리스트
        :param track_type: "단선", "복선-하선", "복선-상선"
        :param track_distance: 복선 시 선로 중심 간격 (m)
        :param track_width: 노반 선로폭 (m)
        """
        try:
            # 1. 파일 초기화
            BVEExporter.initialize_files(save_folder)

            left_slope_file = os.path.join(save_folder, '사면좌.txt')
            right_slope_file = os.path.join(save_folder, '사면우.txt')
            height_file = os.path.join(save_folder, 'height.txt')
            ground_file = os.path.join(save_folder, 'ground.txt')

            # 문자열 버퍼 생성 (I/O 병목 방지용)
            left_lines = []
            right_lines = []
            height_lines = []
            ground_lines = []

            half_w = track_width / 2.0
            side_width = (track_width - track_distance) / 2 #시공기면 폭
            # 2. 인덱스 순서대로 정렬하여 전구간 순회 연산
            sorted_indices = sorted(all_section_results.keys())

            for idx in sorted_indices:
                data = all_section_results[idx]
                if not data:
                    continue

                # np.isnan().any()는 배열이나 튜플 내의 값 중 하나라도 NaN이 있으면 True를 반환합니다.
                try:
                    if np.isnan(data['left']).any() or np.isnan(data['right']).any():
                        continue
                    if np.isnan(data['left_dist']) or np.isnan(data['right_dist']):
                        continue
                except TypeError:
                    # 데이터 타입이 수치가 아닌 다른 객체일 경우 예외 처리 안전 기둥
                    continue
                station = data['station']
                fh_z = data['center'][2]  # 계획고 (FH)

                # 안전장치: data 딕셔너리에 'gl'이나 지반고가 없는 경우 원지반선 중앙 고도 활용
                gh_z = data.get('gl', data['ground'][1][len(data['ground'][1]) // 2])
                diff_h = fh_z - gh_z  # 절성토고

                # 사면 수평 거리 (선로 에지로부터의 폭)
                ld = data['left_dist']
                rd = data['right_dist']

                # 📐 [복선 기하학 오프셋 매퍼] 원점(0,0) 기준 횡방향 좌표 보정
                if track_type == "단선":
                    left_distance = -(half_w + ld)
                    right_distance = (half_w + rd)
                elif track_type == "복선-하선":
                    left_distance = -(side_width + ld)
                    right_distance = (side_width + rd) + track_distance
                elif track_type == "복선-상선":
                    left_distance = -(side_width + ld + track_distance)
                    right_distance = (side_width + rd)
                else:
                    left_distance = -(half_w + ld)
                    right_distance = (half_w + rd)

                # 상대 고도차 계산
                left_level = data['slope_l'][1] - fh_z
                right_level = data['slope_r'][1] - fh_z

                # 3. 각 버퍼 리스트에 문자열 포맷팅 후 적재
                left_lines.append(f"{station},.rail 200; {left_distance:.3f}; {left_level:.3f}; 80;\n")
                right_lines.append(f"{station},.rail 201; {right_distance:.3f}; {right_level:.3f}; 87;\n")
                height_lines.append(f"{station},.height {diff_h:.3f};\n")

                # 성토일 때 0, 절토일 때 3 (지반 텍스처 인덱스 분기 스왑)
                ground_idx = 0 if diff_h > 0 else 3
                ground_lines.append(f"{station},.ground {ground_idx};\n")

            # 4. 🚀 [1초 컷 고속 라이팅] 버퍼링된 데이터를 디스크에 통째로 스트리밍 기록
            with open(left_slope_file, 'w', encoding='utf-8') as f:
                f.writelines(left_lines)

            with open(right_slope_file, 'w', encoding='utf-8') as f:
                f.writelines(right_lines)

            with open(height_file, 'w', encoding='utf-8') as f:
                f.writelines(height_lines)

            with open(ground_file, 'w', encoding='utf-8') as f:
                f.writelines(ground_lines)

        except Exception as e:
            raise e