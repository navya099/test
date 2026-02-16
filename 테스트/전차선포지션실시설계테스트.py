import random
import tkinter as tk
from tkinter import filedialog
import re
import math

class FixedPointEvent:
    """전주 위치가 강제되는 지점 (변전소, 터널 입출구 등)
    Attributes:
        station : 측점
        description: 설명
        max_span_after: 이 이벤트 이후 적용될 최대 경간
    """

    def __init__(self, station, description, max_span_after=50.0):
        self.station = station
        self.description = description
        self.max_span_after = max_span_after

class CatenaryDesignManager:
    """
    노선별 전차선로 설계 매니저
    Attributes:
        start_km: 시작 측점
        end_km : 끝 측점
        curvelist: 곡선정보리스트
        structure_list: 구조물 정보 리스트
        substation_list: 변전설비 정보 리스트

    """
    def __init__(self, start_km, end_km, curvelist, structure_list, substation_list):
        self.start_km = start_km
        self.end_km = end_km
        self.curvelist = curvelist
        self.structure_list = structure_list
        self.substation_list = substation_list
        self.events = []
        self.poledata = {}

    def _generate_events(self):
        """1단계: 노선의 모든 강제 고정점(Events)을 수집 및 정렬"""
        # 시종점
        self.events.append(FixedPointEvent(self.start_km * 1000, "노선 시점"))
        self.events.append(FixedPointEvent(self.end_km * 1000, "노선 종점"))

        # 변전설비 및 에어섹션 (50m 간격 5개 배치 가정)
        for sub in self.substation_list:
            for offset in [-100, -50, 0, 50, 100]:
                self.events.append(FixedPointEvent(sub['km'] * 1000 + offset, f"{sub['type']} 에어섹션"))

        # 터널 입출구 (5m 전 지점 강제 고정)
        for name, start, end in self.structure_list['tunnel']:
            self.events.append(FixedPointEvent(start - 5, "터널 입구 5m 전", max_span_after=40.0))
            self.events.append(FixedPointEvent(end - 5, "터널 출구 5m 전", max_span_after=50.0))

        # 3. 에어조인트(AJ) 배치 (1,600m 간격)
        self._add_air_joint_events(interval=1600)

        # 중복 제거 및 거리순 정렬
        self.events = sorted(list({e.station: e for e in self.events}.values()), key=lambda x: x.station)

    def _add_air_joint_events(self, interval):
        """간섭을 회피하며 에어조인트(AJ) 위치 결정"""
        last_aj_pos = self.start_km * 1000

        while last_aj_pos + interval < self.end_km * 1000:
            target_pos = last_aj_pos + interval

            # 간섭 체크 (구조물 경계 및 변전소 구간)
            # 간섭 발생 시 안전한 장소(토공 일반구간)를 찾을 때까지 50m씩 전진/후진 조정
            offset = 0
            while not self._is_safe_for_aj(target_pos + offset):
                offset -= 50  # 보통 장력을 줄이는 방향(후진)으로 조정하여 안전성 확보
                if target_pos + offset <= last_aj_pos + 100:  # 너무 가까워지면 중단
                    break

            final_aj_pos = target_pos + offset
            # AJ는 장력 구간의 끝과 시작이 겹치므로 3~5경간(약 100~200m)을 점유
            for as_offset in [-100, -50, 0, 50, 100]:
                self.events.append(FixedPointEvent(final_aj_pos + as_offset, "에어조인트(AJ) 구간"))

            last_aj_pos = final_aj_pos

    def _is_safe_for_aj(self, pos):
        """AJ 설치 가능 여부 판단 (토공 구간 & 변전소 이격)"""
        # 1. 구조물 간섭 체크 (터널 내부 및 경계부 50m 이격 권장)
        for name, start, end in self.structure_list['tunnel']:
            if (start - 50) <= pos <= (end + 50):
                return False

        #터널 입출구 회피
        for event in self.events:
            if (event.station - 200) <= pos <= (event.station + 200):
                return False
        # 2. 변전소(AS) 간섭 체크 (변전소 위치 기준 +- 200m 이격)
        for sub in self.substation_list:
            if (sub['km'] * 1000 - 200) <= pos <= (sub['km'] * 1000 + 200):
                return False

        return True  # 모든 간섭 통과

    def _get_limit_span(self, km, default_max):
        """현재 위치의 곡선 반경을 고려한 제한 경간 계산"""
        # [KR 설계기준](https://www.kr.or.kr) 기반 간소화 로직
        # 실제 iscurve() 함수와 연동하여 반경별 max_span 결정
        _,r,c = iscurve(km, self.curvelist)
        return get_max_span_by_radius(r)

    def distribute_poles(self):
        """2단계: 이벤트 구간 사이를 균등 경간으로 채우기"""
        self._generate_events()

        self.all_pos = []
        self.all_spans = []
        self.all_desc = []  # 설명 리스트 추가

        # 초기 시작점 설정
        self.all_pos.append(self.events[0].station)
        self.all_spans.append(0.0) # 첫 지점은 이전 경간이 없음
        self.all_desc.append(self.events[0].description)

        for i in range(len(self.events) - 1):
            start_ev = self.events[i]
            end_ev = self.events[i + 1]

            section_len = end_ev.station - start_ev.station
            if section_len < 0.1: continue

            limit_span = self._get_limit_span(start_ev.station, start_ev.max_span_after)
            num_spans = math.ceil(section_len / limit_span)
            avg_span = round(section_len / num_spans, 3)

            for j in range(1, num_spans + 1):
                if j == num_spans:
                    # 고정점(이벤트 종료 지점) 도달
                    pos = end_ev.station
                    desc = end_ev.description # 이벤트 클래스에 저장된 설명 사용
                else:
                    # 일반 구간 배치
                    pos = round(start_ev.station + (avg_span * j), 4)
                    desc = "일반 구간"

                self.all_pos.append(pos)
                self.all_spans.append(avg_span)
                self.all_desc.append(desc)

        return self.all_spans, self.all_pos

    def save_to_txt(self, file_path):
        """결과 저장 핸들러 (상세 정보 포함)"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 헤더 작성
                f.write("No\t위치(m)\t경간(m)\t곡선반경(R)\t구조물\t비고(설계이벤트)\n")
                f.write("-" * 80 + "\n")

                for i, (pos, span, desc) in enumerate(zip(self.all_pos, self.all_spans, self.all_desc)):
                    # 곡선 및 구조물 정보 조회 (기존 함수 활용)
                    _, radius, _ = iscurve(pos, self.curvelist)
                    structure = isbridge_tunnel(pos, self.structure_list)

                    # 탭 구분자로 깔끔하게 기록
                    f.write(f"{i}\t{pos:.3f}\t{span:.3f}\t{radius}\t{structure}\t{desc}\n")

            print(f"✅ 상세 설계 데이터 저장 완료: {file_path}")
        except Exception as e:
            print(f"❌ 저장 실패: {e}")


def get_max_span_by_radius(radius):
    """곡선 반경(R)에 따른 설계상 최대 경간 제한 (KR CODE 기준 예시)"""
    if radius == 0: return 60      # 직선 구간
    if radius >= 1500: return 60
    if radius >= 1000: return 55
    if radius >= 800: return 50
    if radius >= 600: return 45
    if radius >= 400: return 40
    return 35 # 급곡선
def get_block_index(current_track_position, block_interval=25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval

def iscurve(cur_sta, curve_list):
    """sta가 곡선 구간에 해당하는지 구분하는 함수"""
    rounded_sta = get_block_index(cur_sta)  # 25 단위로 반올림

    for sta, R, c in curve_list:
        if rounded_sta == sta:
            if R == 0:
                return '직선', 0, 0  # 반경이 0이면 직선
            return '곡선', R, c  # 반경이 존재하면 곡선

    return '직선', 0, 0  # 목록에 없으면 기본적으로 직선 처리

def read_file():
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(defaultextension=".txt",
                                           filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")])

    if not file_path:
        print("파일을 선택하지 않았습니다.")
        return []

    print('현재 파일:', file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.read().splitlines()  # 줄바꿈 기준으로 리스트 생성
    except UnicodeDecodeError:
        print('현재 파일은 UTF-8 인코딩이 아닙니다. EUC-KR로 시도합니다.')
        try:
            with open(file_path, 'r', encoding='euc-kr') as file:
                lines = file.read().splitlines()
        except UnicodeDecodeError:
            print('현재 파일은 EUC-KR 인코딩이 아닙니다. 파일을 읽을 수 없습니다.')
            return []

    return lines
def find_last_block(data):
    """
    데이터 리스트에서 마지막 블록 번호(첫 번째 숫자)를 반환.
    예: ['45676,500,0','4646,366,35'] → 4646
    """
    last_block = None

    for line in data:
        if isinstance(line, str):
            # 문자열 맨 앞의 숫자만 추출 (콤마 앞까지)
            match = re.match(r'(\d+)', line)
            if match:
                last_block = int(match.group(1))

    return last_block
def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )

    return file_path
import pandas as pd

def find_structure_section(filepath):
    """xlsx 파일을 읽고 교량과 터널 정보를 반환하는 함수"""
    structure_list = {'bridge': [], 'tunnel': []}

    # xlsx 파일 읽기
    df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

    # 열 개수 확인
    print(df_tunnel.shape)  # (행 개수, 열 개수)
    print(df_tunnel.head())  # 데이터 확인

    # 첫 번째 행을 열 제목으로 설정
    df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
    df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']

    # 교량 구간과 터널 구간 정보
    for _, row in df_bridge.iterrows():
        structure_list['bridge'].append((row['br_NAME'], row['br_START_STA'], row['br_END_STA']))

    for _, row in df_tunnel.iterrows():
        structure_list['tunnel'].append((row['tn_NAME'], row['tn_START_STA'], row['tn_END_STA']))

    return structure_list
def load_structure_data():
    """구조물 데이터를 엑셀 파일에서 불러오는 함수"""
    openexcelfile = open_excel_file()
    if openexcelfile:
        return find_structure_section(openexcelfile)
    else:
        print("엑셀 파일을 선택하지 않았습니다.")
        return None

def load_curve_data():
    """곡선 데이터를 텍스트 파일에서 불러오는 함수"""
    txt_filepath = 'c:/temp/curve_info.txt'
    if txt_filepath:
        return find_curve_section(txt_filepath)
    else:
        print("지정한 파일을 찾을 수 없습니다.")
        return None
def find_curve_section(txt_filepath='curveinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 곡선반경(radius) 정보를 반환하는 함수"""

    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius', 'cant'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius'], row['cant']))

    return curve_list
def read_polyline(file_path):
    points = []
    with open(file_path, 'r') as file:
        for line in file:
            # 쉼표로 구분된 값을 읽어서 float로 변환
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points
def load_coordinates():
    """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
    coord_filepath = 'c:/temp/bve_coordinates.txt'
    return read_polyline(coord_filepath)
def get_dat():
    # 파일 읽기 및 데이터 처리

    data = read_file()
    last_block = find_last_block(data)
    start_km = 0
    end_km = last_block // 1000

    # 구조물 정보 로드
    structure_list = load_structure_data()
    if structure_list:
        print("구조물 정보가 성공적으로 로드되었습니다.")

    # 곡선 정보 로드
    curvelist = load_curve_data()
    if curvelist:
        print("곡선 정보가 성공적으로 로드되었습니다.")

    # BVE 좌표 로드
    polyline = load_coordinates()
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]
    return start_km, end_km, structure_list, curvelist, polyline_with_sta


def write_txt(poledata, file_path):
    """
    poledict(딕셔너리) 데이터를 텍스트 파일로 저장
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # 헤더(Header) 작성: 엑셀에서 열 때 컬럼 구분을 위해 추가
            header = "위치(km)\t경간(m)\t곡선여부\tR\tC\t급전구간\t구조물"
            f.write(header + "\n")

            # poledata의 각 항목(리스트)을 탭으로 구분하여 저장
            for pos in sorted(poledata.keys()):
                line_data = poledata[pos]
                # 리스트 내의 모든 요소를 문자열로 변환 후 탭으로 연결
                line_str = "\t".join(map(str, line_data))
                f.write(line_str + "\n")

        print(f"전주 데이터 저장 완료: {file_path}")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")


def design_catenary_stations(line_length_km):
    # 설계 기준 (단위: km)
    ss_interval = 45  # 변전소 간격 표준
    ssp_interval = 12  # 보조구분소 간격 표준

    stations = []

    # 1. 변전소(SS) 위치 결정 (시점과 종점 부근 배치)
    # 87km의 경우, 20km 지점과 65km 지점 등에 배치하여 부하 분산
    ss_locations = [20, 65]
    for loc in ss_locations:
        stations.append({"type": "SS (변전소)", "km": loc})

    # 2. 구분소(SP) 위치 결정 (두 변전소의 중앙)
    sp_location = sum(ss_locations) / 2
    stations.append({"type": "SP (구분소)", "km": sp_location})

    # 3. 보조구분소(SSP) 위치 결정
    # 0~SS1, SS1~SP, SP~SS2, SS2~87 사이 구간에 배치
    check_points = [0] + sorted([s['km'] for s in stations]) + [line_length_km]

    for i in range(len(check_points) - 1):
        dist = check_points[i + 1] - check_points[i]
        if dist > ssp_interval:
            num_ssp = int(dist // ssp_interval)
            step = dist / (num_ssp + 1)
            for j in range(1, num_ssp + 1):
                stations.append({"type": "SSP (보조구분소)", "km": round(check_points[i] + (step * j), 2)})

    # 거리순 정렬
    stations = sorted(stations, key=lambda x: x['km'])
    return stations

def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'

    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'

    return '토공'


def create_pole_infodata(spans, pos_list, curvelist, substation_list, structure_list):
    poledict = {}

    for span, pos in zip(spans, pos_list):
        # 1. 현재 위치(pos)가 어느 급전 구간에 있는지 찾기
        current_section = "종점 이후"
        for i in range(len(substation_list)):
            if pos <= substation_list[i]['km']:
                # 현재 위치가 특정 스테이션 이전이라면, 해당 스테이션을 향하는 구간으로 정의
                target_station = substation_list[i]
                current_section = f"~{target_station['km']}km({target_station['type']})"
                break
            elif i == len(substation_list) - 1:
                # 마지막 스테이션을 지난 경우
                current_section = f"{substation_list[i]['km']}km 이후"

        # 2. 곡선 및 구조물 정보 조회 (기존 로직)
        current_curve, r, c = iscurve(pos, curvelist)
        current_structure = isbridge_tunnel(pos, structure_list)

        # 3. 데이터 저장
        poledict[pos] = [pos, span, current_curve, r, c, current_section, current_structure]

    return poledict


def main():
    start_km, end_km, structure_list, curvelist, polyline_with_sta = get_dat()
    substation_list = design_catenary_stations(line_length_km=end_km)
    mgr = CatenaryDesignManager(start_km, end_km, curvelist, structure_list, substation_list)
    all_spans, all_pos = mgr.distribute_poles()
    mgr.save_to_txt('c:/temp/test.txt')
    print('완료')
if __name__ == '__main__':
    main()

