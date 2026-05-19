import os


class BVEExporter:
    """BVE 구문 익스포터 (OpenBVE 노선 뼈대 스크립트 자동 생성)"""

    @staticmethod
    def initialize_files(save_folder):
        """출력 파일이 기존에 존재한다면 초기화(삭제)"""
        left_slope_file = os.path.join(save_folder, '사면좌.txt')
        right_slope_file = os.path.join(save_folder, '사면우.txt')

        for filepath in [left_slope_file, right_slope_file]:
            if os.path.exists(filepath):
                os.remove(filepath)

    @staticmethod
    def export_section(save_folder, data, use_relative_height=True):
        """
        현재 섹션의 사면 위치를 BVE 타겟 레일 구문(.rail)으로 누적 저장
        :param save_folder: 텍스트 파일이 저장될 폴더 경로
        :param data: SectionProvider의 단면 데이터 딕셔너리
        :param use_relative_height: True일 경우 선로 계획고(FH) 기준 상대 높이로 추출, False면 절대 고도
        """
        try:
            # 출력 파일 경로 설정
            left_slope_file = os.path.join(save_folder, '사면좌.txt')
            right_slope_file = os.path.join(save_folder, '사면우.txt')

            # 기본 변수 파싱
            station = data['station']
            track_width = data['track_width']
            fh_z = data['center'][2]  # 선로 중심 계획고 (FH)

            # 사면 수평 거리 (절대값 수치)
            ld = data['left_dist']
            rd = data['right_dist']

            # 🚨 [기하학적 부호 교정] 선로 중심(0) 기준 수평 오프셋 계산
            # 좌측 공간은 음수(-), 우측 공간은 양수(+)
            left_distance = -(track_width / 2.0 + ld)
            right_distance = (track_width / 2.0 + rd)

            # 🚨 [고도값 교정] BVE 환경에 맞춘 높이 산정
            if use_relative_height:
                # 선로 계획고를 0으로 둔 상대적 높이 (일반적인 BVE 오브젝트 빌드 방식)
                left_level = data['slope_l'][1] - fh_z
                right_level = data['slope_r'][1] - fh_z
            else:
                # DEM 절대 고도 원본값
                left_level = data['slope_l'][1]
                right_level = data['slope_r'][1]

            # -------------------------------------------------------------
            # 1. 좌측사면 추출: 🚨 모드를 'w'에서 'a'(Append)로 변경하여 데이터 누적
            # -------------------------------------------------------------
            with open(left_slope_file, 'a', encoding='utf-8') as f:
                # 구문 끝 주석 처리 및 소수점 3자리 포맷팅으로 가독성 확보
                f.write(f"{station}, .rail 200; {left_distance:.3f}; {left_level:.3f}; 86;\n")

            # -------------------------------------------------------------
            # 2. 우측사면 추출: 🚨 모드를 'a'로 변경
            # -------------------------------------------------------------
            with open(right_slope_file, 'a', encoding='utf-8') as f:
                f.write(f"{station}, .rail 201; {right_distance:.3f}; {right_level:.3f}; 87;\n")

        except Exception as e:
            raise e