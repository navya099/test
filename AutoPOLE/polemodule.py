import sys
sys.path.append("D:\문서\chatgpt성과\python\BVEParser")
from BVEclass import Vector3  # BVE CLASS Vector3로드
from enum import Enum


class AirJoint(Enum):
    START = "에어조인트 시작점 (1호주)"
    POINT_2 = "에어조인트 (2호주)"
    MIDDLE = "에어조인트 중간주 (3호주)"
    POINT_4 = "에어조인트 (4호주)"
    END = "에어조인트 끝점 (5호주)"


class PolePositionManager:
    def __init__(self, dataLoader):
        self.data = dataLoader
        self.mode = mode
        self.start_km = start_km
        self.end_km = end_km
        self.pole_positions = []
        self.airjoint_list = []
        self.post_number_lst = []
        self.posttype_list = []
        self.total_data_list = []

    def generate_positions(self):
        if self.mode == 1:
            self.pole_positions = distribute_pole_spacing_flexible(self.start_km, self.end_km)
            self.airjoint_list = define_airjoint_section(self.pole_positions)
            self.post_number_lst = generate_postnumbers(self.pole_positions)
        else:
            # Load from file
            messagebox.showinfo('파일 선택', '사용자 정의 전주파일을 선택해주세요')

            self.load_pole_positions_from_file()
            logger.info('사용자 정의 전주파일이 입력되었습니다.')

    def load_pole_positions_from_file(self) -> None:
        """txt 파일을 읽고 곧바로 '측점', '전주번호', '타입', '에어조인트' 정보를 반환하는 함수"""

        data_list = []
        positions = []
        post_number_list = []
        type_list = []
        airjoint_list = []

        # 텍스트 파일(.txt) 읽기
        self.txtfile_handler.select_file("미리 정의된 전주 파일 선택", [("txt files", "*.txt"), ("All files", "*.*")])
        txt_filepath = self.txtfile_handler.get_filepath()

        df_curve = pd.read_csv(txt_filepath, sep=",", header=0, names=['측점', '전주번호', '타입', '에어조인트'])

        # 곡선 구간 정보 저장
        self.total_data_list = df_curve.to_records(index=False).tolist()
        self.pole_positions = df_curve['측점'].tolist()
        self.post_number_lst = list(zip(df_curve['측점'], df_curve['전주번호']))
        self.posttype_list = list(zip(df_curve['측점'], df_curve['타입']))
        self.airjoint_list = [(row['측점'], row['에어조인트']) for _, row in df_curve.iterrows() if row['에어조인트'] != '일반개소']

    # GET 메소드 추가
    def get_all_pole_data(self):
        """전주 관련 모든 데이터를 반환"""
        return {
            "pole_positions": self.pole_positions,
            "airjoint_list": self.airjoint_list,
            "post_number_lst": self.post_number_lst,
            "posttype_list": self.posttype_list,
            "total_data_list": self.total_data_list,
        }

    def get_pole_positions(self):
        return self.pole_positions

    def get_airjoint_list(self):
        return self.airjoint_list

    def get_post_number_lst(self):
        return self.post_number_lst

    def get_post_type_list(self):
        return self.posttype_list

    def get_total_data_list(self):
        return self.total_data_list


class PoleDATAManager:  # 전체 총괄
    def __init__(self):
        self.poles = []  # 개별 pole 데어터를 저장할 리스트
        poledata = PoleDATA()  # 인스턴스 생성
        self.poles.append(poledata)  # 리스트에 인스턴스 추가


class PoleDATA:  # 기둥 브래킷 금구류 포함 데이터
    def __init__(self):
        self.Poleattributes = MastDATA()  # 기둥 요소
        self.Brackets = []  # 브래킷을 담을 리스트
        bracketdata = BracketElement()  # 인스턴스 생성
        self.Brackets.append(bracketdata)  # 리스트에 인스턴스 추가
        self.pos = 0.0  # station
        self.post_number = ''
        self.current_curve = ''
        self.radius = 0.0
        self.cant = 0.0
        self.current_structure = ''
        self.current_pitch = 0.0
        self.current_airjoint = ''
        self.gauge = 0.0
        self.span = 0.0
        self.coord = Vector3(0, 0, 0)
        self.ispreader = False


class BracketElement:
    def __init__(self):
        self.name = ''
        self.index = 0
        self.type = ''
        self.positionx = 0.0
        self.positiony = 0.0


class MastDATA:
    def __init__(self):
        self.name = ''
        self.index = 0
        self.type = ''
        self.height = 0.0
        self.width = 0.0
        self.fundermentalindex = 0
        self.fundermentaltype = ''
        self.fundermentaldimension = 0.0


class FeederDATA:
    def __init__(self):
        self.name = ''
        self.index = 0
        self.x = 0.0
        self.y = 0.0
