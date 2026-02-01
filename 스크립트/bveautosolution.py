import time

from bve곡선레일구문생성기 import preprocess_input_index, extract_cant, create_freeobj,\
    cal_mainlogic, save_files, create_railtype, save_railtype
from 거리표이미지생성기 import create_km_object
from 곡선표이미지생성기 import process_curve_data, create_curve_post_txt, create_curve_index_txt, create_speed_limit
from 교량터널구문생성기 import get_designspeed, get_linecount, load_structure_data, create_network_data, create_txt
import os
import random

from 기울기표이미지생성기 import process_bve_profile, create_pitch_post_txt, create_pitch_index_txt
from 랜덤신호위치생성 import save_signal_data
from 랜덤전주위치생성 import distribute_pole_spacing_flexible, load_curve_data, load_pitch_data,\
    load_coordinates, define_airjoint_section, generate_postnumbers, save_pole_data, save_wire_data
from 자동통신구문생성 import create_transmisson_data

from file_io_utils import copy_files
from file_io_utils import copy_all_files

def get_float_input(prompt):
    while 1:
        try:
            return float(input(prompt))
        except ValueError:
            raise ValueError('숫자만 입력하세요')

class SolutionRunner:
    def __init__(self, logger=print):
        self.offset = None
        self.brokenchain = None
        self.last_block = None
        self.start_blcok = None
        self.base_source_directory = 'c:/temp/'  # 원본 소스 기본 경로
        self.structure_list = None
        self.linecount = None
        self.logger = logger
        self.designspeed = None
        self.railtype_map = {120: '도시철도', 150: '일반철도', 250: '준고속철도', 350: '고속철도'}
        self.alignment_type = ''
        self.path = r'D:/BVE/루트/Railway/Route/연습용루트/'
        self.obj_path = r'D:/BVE/루트/Railway/Object/abcdefg/'

    def log(self, msg):
        self.logger(msg)

    def run(self):
        try:
            self.load_info() #기본정보
            self.run_bridge()#교량터널구조물
            self.run_curve()#곡선레일
            self.run_pole()#전차선
            self.run_signal()#신호
            self.run_post()#포스트
            self.run_transmission()#통신
            self.log("전체 작업 완료")

        except Exception as e:
            self.log(f"[오류] {str(e)}")

    def load_info(self):
        self.log(f"{'-' * 5}기본 정보 로드 시작{'-' * 5}")
        try:

            self.designspeed = get_designspeed()
            self.linecount = get_linecount()
            self.alignment_type = self.railtype_map.get(self.designspeed)
            self.log(f"로드된 정보 : 설계속도 : {self.designspeed}km/h, 선로구분: {self.alignment_type} , 선로수 {self.linecount}개")
            self.curve_info = load_curve_data()
            if not self.curve_info:
                self.log("곡선 정보 로드에 실패했습니다.")
            # 기울기 정보 로드
            self.pitch_info = load_pitch_data()
            if not self.pitch_info:
                self.log("기울기 정보 로드에 실패했습니다.")
            self.bve_coord = load_coordinates()
            # 구조물 정보 로드
            self.structure_list = load_structure_data()
            if not self.structure_list:
                self.log("구조물 정보 로드에 실패했습니다.")

            self.start_blcok = self.curve_info[0][0]
            self.last_block = self.curve_info[-1][0]
            self.log(f' 시작 측점 : {self.start_blcok}, 끝 측점 : {self.last_block}')


            self.brokenchain = 0.0
            self.offset = 0.0

            self.log(f'파정 : {self.brokenchain}, freeobj x 오프셋 : {self.offset}')
            self.log("기본 정보 로드 완료")
        except Exception as e:
            self.log(f'기본 정보 로드중 오류가 발생했습니다. {e}')

    def run_bridge(self):
        """#교량터널구조물"""
        self.log(f"{'-' * 5}# 1. 교량터널구조물 생성 시작{'-' * 5}")
        # 구문생성
        try:
            result = create_network_data(self.structure_list, self.designspeed, self.linecount)
            # txt저장
            output_file = os.path.join(self.path, '구조물.txt')
            create_txt(output_file, result)
            # 최종 출력
            self.log('교량터널구조물 생성이 완료되었습니다.')
        except Exception as e:
            self.log(f'교량터널구조물 생성중 오류가 발생했습니다. {e}')

    def run_curve(self):
        self.log(f"{'-' * 5} # 2. 곡선레일 생성 시작{'-' * 5}")
        try:
            index_dict = preprocess_input_index(self.alignment_type, mode='default')
            cant_list = extract_cant(self.curve_info)
            freeobj = cal_mainlogic(self.curve_info, cant_list)

            content = create_freeobj(freeobj, self.structure_list, self.curve_info, index_dict)
            save_path = os.path.join(self.path, 'freeobj.txt')
            save_files(content, save_path)

            railtype = create_railtype(self.curve_info, self.structure_list, index_dict)
            save_path = os.path.join(self.path, 'railtype.txt')
            save_railtype(railtype, save_path)
            self.log("FreeObj 및 RailType 생성이 완료되었습니다.")
        except Exception as e:
            self.log(f"곡선레일 생성 중 오류가 발생했습니다. {e}")

    def run_pole(self):
        self.log(f"{'-' * 5} #3. 전차선 생성 시작{'-' * 5}")
        try:
            """전체 작업을 관리하는 메인 함수"""
            # 파일 읽기 및 데이터 처리
            last_block = self.curve_info[-1][0]
            start_km = 0
            end_km = last_block // 1000
            spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km)

            airjoint_list = define_airjoint_section(pole_positions)

            # 전주번호 추가
            post_number_lst = generate_postnumbers(pole_positions)

            # 데이터 저장
            #전주파일
            polefile = os.path.join(self.path, '전주.txt')
            wirefile = os.path.join(self.path, '전차선.txt')
            save_pole_data(pole_positions, self.structure_list, self.curve_info, self.pitch_info, self.designspeed, airjoint_list, self.bve_coord, polefile)
            save_wire_data(self.designspeed, pole_positions, spans, self.structure_list,self.curve_info, self.pitch_info, self.bve_coord, airjoint_list, wirefile)
            # 최종 출력
            self.log(f"생성된 전주 개수: {len(pole_positions)}, 에어조인트 구간 갯수: {len(airjoint_list)}")
            self.log("전주와 전차선 생성이 완료됐습니다.")
        except Exception as e:
            self.log(f"전주와 전차선 처리에서 문제가 발생했습니다. {e}")


    def run_signal(self):
        self.log(f"{'-' * 5} #4. 신호 생성 시작{'-' * 5}")
        # 파일 읽기 및 데이터 처리
        # 랜덤 범위로 간격을 생성 (1200~1800 사이의 랜덤 값)
        try:
            block_length = [random.randint(1200, 1800) for _ in range(4)]
            last_block = self.curve_info[-1][0]
            start_km = 0
            end_km = last_block // 1000
            spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km, block_length)

            # 데이터 저장
            signalpath = os.path.join(self.path, '신호.txt')
            save_signal_data(pole_positions, self.structure_list, signalpath)

            # 최종 출력

            self.log(f"신호기 개수: {len(pole_positions)}")
            self.log(f'폐색간격 최소:{min(block_length)},최대: {max(block_length)}')

            self.log("신호 생성 완료")
        except Exception as e:
            self.log(f"신호 처리에서 문제가 발생했습니다. {e}")

    def run_post(self):
        self.log(f"{'-' * 5} #6. 선로제표 생성 시작{'-' * 5}")
        try:
            self.create_km_post()
            self.create_curve_post()
            self.create_pitch_post()
            self.create_structure_post()
            self.log("선로제표 생성이 완료되었습니다.")
        except Exception as e:
            self.log(f"제표 처리에서 문제가 발생했습니다. {e}")

    def run_transmission(self):
        self.log(f"{'-' * 5} #5. 통신구문 생성 시작{'-' * 5}")
        # 구문생성
        try:
            result = create_transmisson_data(self.structure_list)

            # txt저장
            output_file = os.path.join(self.path, '통신.txt')
            create_txt(output_file, result)
            # 최종 출력
            self.log("통신 생성 완료")
        except Exception as e:
            self.log(f"통신 구문 처리에서 문제가 발생했습니다. {e}")

    def create_km_post(self):
        self.log(f"{'-' * 5} #6-1. 거리표 생성 시작{'-' * 5}")

        try:
            # 디렉토리 설정
            self.work_directory = 'c:/temp/km_post/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)

            self.target_directory = os.path.join(self.obj_path, 'km_post')

            #노선 종류 입력받기

            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory,'km_post/소스/', self.alignment_type) + '/'

            intervel = 100 if self.alignment_type == '도시철도' else 200
            index_datas, post_datas = create_km_object(self.start_blcok, self.last_block, self.structure_list, intervel, self.alignment_type, self.source_directory, self.work_directory, self.target_directory, self.offset)

            index_file = os.path.join(self.work_directory, 'km_index.txt')
            post_file = os.path.join(self.work_directory, 'km_post.txt')

            create_txt(index_file, index_datas)

            create_txt(post_file, post_datas)

            copy_files([index_file, post_file], self.path)
            copy_all_files(self.source_directory, self.target_directory, ['.jpg', '.jpeg'],['.csv', '.png', '.txt'],
                           delete_source=False, delete_target=False)
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt', '.jpg', '.jpeg'], ['.dxf', '.ai'])

            self.log("거리표 생성이 완료되었습니다.")

        except Exception as e:
            self.log(f"거리표 생성 중 오류가 발생했습니다:\n{e}")

    def create_curve_post(self):
        self.log(f"{'-' * 5} #6-2. 곡선표 생성 시작{'-' * 5}")
        try:
            # 디렉토리 설정
            self.work_directory = 'c:/temp/curve/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)

            self.target_directory = os.path.join(self.obj_path, 'curve_post')

            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory,'curve/소스/', self.alignment_type) + '/'

            objectdatas = process_curve_data(self.source_directory, self.work_directory, self.target_directory, self.curve_info,
                                             self.structure_list, self.brokenchain, self.alignment_type, 'BVE', self.offset)

            # 최종 텍스트 생성
            if objectdatas:
                post_file = os.path.join(self.work_directory, 'curve_post.txt')
                index_file = os.path.join(self.work_directory, 'curve_index.txt')
                create_curve_post_txt(objectdatas, post_file)
                create_curve_index_txt(objectdatas, index_file)
                create_speed_limit(objectdatas, self.work_directory)

            copy_files([index_file, post_file], self.path)
            copy_all_files(self.source_directory, self.target_directory, ['.jpg', '.jpeg'],
                           delete_source=False, delete_target=False)
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt', '.jpg', '.jpeg'], ['.dxf', '.ai'])

            self.log("✅ 곡선표 생성이 성공적으로 완료되었습니다.")


        except Exception as e:
            self.log(f"곡선표 생성 중 오류가 발생했습니다:\n{e}")

    def create_pitch_post(self):
        self.log(f"{'-' * 5} #6-3. 기울기표 생성 시작{'-' * 5}")
        try:

            self.work_directory = 'c:/temp/pitch/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)

            self.target_directory = os.path.join(self.obj_path, 'pitch_post')

            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory,'pitch/소스/', self.alignment_type) + '/'

            from 기울기표이미지생성기 import process_and_save_sections
            vipdatas = process_and_save_sections(self.pitch_info, self.brokenchain, 'BVE', self.pitch_info)

            objectdatas = process_bve_profile(vipdatas, self.structure_list, self.source_directory, self.work_directory,
                                              self.target_directory,self.alignment_type, offset=self.offset)

            # 최종 텍스트 생성
            if objectdatas:

                post_file = os.path.join(self.work_directory, 'pitch_post.txt')
                index_file = os.path.join(self.work_directory, 'pitch_index.txt')
                create_pitch_post_txt(objectdatas, post_file)
                create_pitch_index_txt(objectdatas, index_file)

            copy_files([index_file, post_file], self.path)
            copy_all_files(self.source_directory, self.target_directory, ['.jpg', '.jpeg'],
                           delete_source=False, delete_target=False)
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt', '.jpg', '.jpeg'], ['.dxf', '.ai'])

            self.log("✅ 기울기표 생성이 성공적으로 완료되었습니다.")

        except Exception as e:
            self.log( f"기울가표 생성 중 오류가 발생했습니다:\n{e}")

    def create_structure_post(self):
        self.log(f"{'-' * 5} #6-4. 구조물표 생성 시작{'-' * 5}")
        self.log('정보: 구조물표 구현은 현재 미구현된 상태입니다.')

if __name__ == '__main__':
    runner = SolutionRunner()
    start = time.time()
    runner.load_info()       # 기본 정보 로드
    runner.run_bridge()      # 교량/터널 구문 생성
    runner.run_curve()       # 곡선 레일 생성
    runner.run_pole()        # 전차선 생성
    runner.run_signal()      # 신호 생성
    runner.run_transmission()  # 통신 생성
    runner.run_post()        # 포스트 생성
    end = time.time()
    elapsed = end - start
    runner.log(f"전체 작업 완료! 소요시간 : {elapsed:.2f}초")