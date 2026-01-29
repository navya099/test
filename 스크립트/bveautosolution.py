import time

from bve곡선레일구문생성기 import preprocess_input_index, extract_cant, create_freeobj, \
    cal_mainlogic, save_files, create_railtype, save_railtype
from 거리표이미지생성기 import select_target_directory, copy_all_files, create_km_object, apply_brokenchain_to_structure
from 곡선표이미지생성기 import process_curve_data, create_curve_post_txt, create_curve_index_txt, create_speed_limit
from 교량터널구문생성기 import get_designspeed, get_linecount, load_structure_data, create_network_data, create_txt, \
    find_structure_section
import os
import random

from 기울기표이미지생성기 import process_bve_profile, create_pitch_post_txt, create_pitch_index_txt
from 랜덤신호위치생성 import save_signal_data
from 랜덤전주위치생성 import distribute_pole_spacing_flexible, load_curve_data, load_pitch_data, \
    load_coordinates, define_airjoint_section, generate_postnumbers, save_pole_data, save_wire_data
from 자동통신구문생성 import create_transmisson_data


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
        self.obj_path = r'D:\BVE\루트\Railway\Object\abcdefg/'

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
        self.log("기본 정보 로드 시작")
        self.designspeed = get_designspeed()
        self.linecount = get_linecount()
        self.alignment_type = self.railtype_map.get(self.designspeed)
        self.log(f"로드된 정보 : 설계속도 : {self.designspeed}km/h, 선로구분: {self.alignment_type} , 선로수 {self.linecount}개")
        self.curve_info = load_curve_data()
        if self.curve_info:
            self.log("곡선 정보가 성공적으로 로드되었습니다.")
        # 기울기 정보 로드
        self.pitch_info = load_pitch_data()
        if self.pitch_info:
            self.log("기울기선 정보가 성공적으로 로드되었습니다.")
        self.bve_coord = load_coordinates()
        # 구조물 정보 로드
        self.structure_list = load_structure_data()
        if self.structure_list:
            self.log("구조물 정보가 성공적으로 로드되었습니다.")

        self.start_blcok = self.curve_info[0][0]
        self.last_block = self.curve_info[-1][0]
        self.log(f' 시작 측점 : {self.start_blcok}, 끝 측점 : {self.last_block}')


        self.brokenchain = 0.0
        self.offset = 0.0

        self.log(f'파정 : {self.brokenchain}, freeobj x 오프셋 : {self.offset}')
        self.log("기본 정보 로드 완료")

    def run_bridge(self):
        """#교량터널구조물"""
        self.log("교량터널구조물 생성 시작")
        # 구문생성
        result = create_network_data(self.structure_list, self.designspeed, self.linecount)
        # txt저장
        output_file = os.path.join(self.path, '교량터널.txt')
        create_txt(output_file, result)
        # 최종 출력
        self.log('교량터널구조물 생성이 완료되었습니다.')

    def run_curve(self):
        self.log("곡선레일 생성 시작")
        try:
            index_dict = preprocess_input_index(self.alignment_type, mode='default')
            self.log("파일을 읽는 중...")

            self.log("캔트 정보 추출 중...")
            cant_list = extract_cant(self.curve_info)

            self.log("FreeObj 계산 중...")
            freeobj = cal_mainlogic(self.curve_info, cant_list)

            self.log("FreeObj 생성 중...")
            content = create_freeobj(freeobj, self.structure_list, self.curve_info, index_dict)
            save_path = os.path.join(self.path, 'freeobj.txt')
            save_files(content, save_path)
            self.log("FreeObj 저장 완료!")

            self.log("Railtype 생성 중...")
            railtype = create_railtype(self.curve_info, self.structure_list, index_dict)
            save_path = os.path.join(self.path, 'railtype.txt')
            save_railtype(railtype, save_path)
            self.log("Railtype 저장 완료!")

            self.log("FreeObj 및 RailType 생성이 완료되었습니다.")
        except Exception as e:
            self.log(f"[오류] {str(e)}")

    def run_pole(self):
        self.log("전차선 생성 시작")

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
        self.log("전주와 전차선 txt가 성공적으로 저장되었습니다.")

        # 최종 출력
        self.log(f"전주 개수: {len(pole_positions)}")
        self.log(f"마지막 전주 위치: {pole_positions[-1]}m (종점: {int(end_km * 1000)}m)")
        self.log('모든 작업 완료')
        self.log("전차선 생성 완료")

    def run_signal(self):
        self.log("신호 생성 시작")
        # 파일 읽기 및 데이터 처리
        # 랜덤 범위로 간격을 생성 (1200~1800 사이의 랜덤 값)

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

    def run_post(self):
        self.log("포스트 생성 시작")

        self.create_km_post()
        self.create_curve_post()
        self.create_pitch_post()
        self.create_structure_post()
        self.log("포스트 생성 완료")

    def run_transmission(self):
        self.log("통신 생성 시작")
        # 구문생성
        result = create_transmisson_data(self.structure_list)

        # txt저장
        output_file = os.path.join(self.path, '통신.txt')
        create_txt(output_file, result)
        # 최종 출력
        self.log('구문 생성이 완료되었습니다.')
        self.log("통신 생성 완료")

    def create_km_post(self):
        self.log('거리표 생성 시작')

        try:
            # 디렉토리 설정
            self.log("작업 디렉토리 확인 중...")
            self.work_directory = 'c:/temp/km_post/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)
                self.log(f"디렉토리 생성: {self.work_directory}")
            else:
                self.log(f"디렉토리 존재: {self.work_directory}")

            # 대상 디렉토리 선택
            self.log("대상 디렉토리 선택 중...")
            self.target_directory = os.path.join(self.obj_path, 'km_post')
            self.log(f"대상 디렉토리: {self.target_directory}")

            #노선 종류 입력받기

            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory,'km_post/소스/', self.alignment_type) + '/'
            self.log(f"소스 경로: {self.source_directory}")

            intervel = 100 if self.alignment_type == '도시철도' else 200
            self.log("KM Object 생성 중...")
            index_datas, post_datas = create_km_object(self.start_blcok, self.last_block, self.structure_list, intervel, self.alignment_type, self.source_directory, self.work_directory, self.target_directory, self.offset)

            index_file = os.path.join(self.work_directory, 'km_index.txt')
            post_file = os.path.join(self.work_directory, 'km_post.txt')

            self.log(f"파일 작성: {index_file}")
            create_txt(index_file, index_datas)

            self.log(f"파일 작성: {post_file}")
            create_txt(post_file, post_datas)

            self.log("txt 작성이 완료됐습니다.")

            # 파일 복사
            self.log("결과 파일 복사 중...")
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])

            self.log("모든 작업이 완료됐습니다.")
            self.log("KM Object 생성이 완료되었습니다.")

        except Exception as e:
            self.log(f"[오류] {str(e)}")
            self.log(f"작업 중 오류가 발생했습니다:\n{e}")

    def create_curve_post(self):
        self.log('곡선표 생성 시작')
        try:
            # 디렉토리 설정
            self.log("작업 디렉토리 확인 중...")
            self.work_directory = 'c:/temp/curve/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)
                self.log(f"디렉토리 생성: {self.work_directory}")
            else:
                self.log(f"디렉토리 존재: {self.work_directory}")

            # 대상 디렉토리 선택
            self.log("대상 디렉토리 선택 중...")
            self.target_directory = os.path.join(self.obj_path, 'curve_post')
            self.log(f"대상 디렉토리: {self.target_directory}")

            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory,'curve/소스/', self.alignment_type) + '/'
            self.log(f"소스 경로: {self.source_directory}")

            # 곡선 정보 파일 읽기
            self.log("곡선 정보 파일 읽는 중...")

            # 곡선 데이터 처리
            self.log("곡선 데이터 처리 중...")
            objectdatas = process_curve_data(self.source_directory, self.work_directory, self.target_directory, self.curve_info,
                                             self.structure_list, self.brokenchain, self.alignment_type, 'BVE', self.offset)

            # 최종 텍스트 생성
            if objectdatas:
                self.log("최종 결과 생성 중...")
                create_curve_post_txt(objectdatas, self.work_directory)
                create_curve_index_txt(objectdatas, self.work_directory)
                create_speed_limit(objectdatas, self.work_directory)
                self.log("결과 파일 생성 완료!")

            # 파일 복사
            self.log("결과 파일 복사 중...")
            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])

            self.log("✅ 모든 작업이 성공적으로 완료되었습니다.")


        except Exception as e:
            self.log(f"[오류] {str(e)}")
    def create_pitch_post(self):
        self.log('기울기표 생성 시작')
        try:
            # 디렉토리 설정
            self.log("작업 디렉토리 확인 중...")
            self.work_directory = 'c:/temp/pitch/result/'
            if not os.path.exists(self.work_directory):
                os.makedirs(self.work_directory)
                self.log(f"디렉토리 생성: {self.work_directory}")
            else:
                self.log(f"디렉토리 존재: {self.work_directory}")

            # 대상 디렉토리 선택
            self.log("대상 디렉토리 선택 중...")
            self.target_directory = os.path.join(self.obj_path, 'pitch_post')
            self.log(f"대상 디렉토리: {self.target_directory}")

            # ✅ 항상 base_source_directory에서 새로 경로 만들기
            self.source_directory = os.path.join(self.base_source_directory,'pitch/소스/', self.alignment_type) + '/'
            self.log(f"소스 경로: {self.source_directory}")

            from 기울기표이미지생성기 import process_and_save_sections
            vipdatas = process_and_save_sections(self.pitch_info, self.brokenchain, 'BVE', self.pitch_info)

            objectdatas = process_bve_profile(vipdatas, self.structure_list, self.source_directory, self.work_directory,
                                              self.target_directory,self.alignment_type, offset=self.offset)

            # 최종 텍스트 생성
            if objectdatas:
                self.log("최종 결과 생성 중...")
                create_pitch_post_txt(objectdatas, self.work_directory)
                create_pitch_index_txt(objectdatas, self.work_directory)
                self.log("결과 파일 생성 완료!")
            self.log("BVE 작업 완료")

            copy_all_files(self.work_directory, self.target_directory, ['.csv', '.png', '.txt'], ['.dxf', '.ai'])
            self.log("모든 작업이 완료되었습니다.")

            self.log( "Pitch 데이터 처리가 성공적으로 완료되었습니다.")

        except Exception as e:
            self.log( f"처리 중 오류가 발생했습니다:\n{e}")

    def create_structure_post(self):
        pass

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