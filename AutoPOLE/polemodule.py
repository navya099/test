sys.path.append("D:\문서\chatgpt성과\python\BVEParser")
from BVEclass import Vector3  # BVE CLASS Vector3로드


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
