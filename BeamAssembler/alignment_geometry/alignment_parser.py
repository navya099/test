import math

from utils.funtion import try_parse_int, try_parse_float
from alignment_geometry.rail import Rail
from alignment_geometry.form import Form
from alignment_geometry.curve import Curve

class AlignmentParser:
    def __init__(self):
        self.lines: list[str] = []
        self.line: str = ''
        self.linenumber: int = 0

    def _parse_line(self):
        """공통 파싱: station과 components 리스트 추출"""
        parts = self.line.split(',', 1)
        if len(parts) < 2:
            print(f"형식 오류: 줄 {self.linenumber}: {self.line}")
            return 0.0, []

        try:
            station = float(parts[0])
        except ValueError:
            print(f"ValueError: 줄 {self.linenumber} station parsing 실패")
            station = 0.0

        info = parts[1].strip().split(' ', 1)
        if len(info) < 2:
            print(f"형식 오류: 줄 {self.linenumber}: {self.line}")
            return station, []

        components = info[1].split(';')
        return station, components

    def parse_line(self, parse_func, cls):
        """
        제네릭 파서
        parse_func: components -> 필요한 값 반환
        cls: 생성할 도메인 클래스(Rail, Form, Curve 등)
        return: 생성한 클래스 객체
        """
        station, components = self._parse_line()
        block_index = int(math.floor(station / 25 + 0.001)) #내림처리
        station = block_index * 25
        if not components:
            return 0

        try:
            parsed_values = parse_func(components)
        except Exception as e:
            print(f"{cls.__name__} 파싱 실패: {e}")
            # 안전값 반환
            if cls.__name__ == "Rail":
                parsed_values = (0, 0.0, 0.0, 0)
            elif cls.__name__ == "Form":
                parsed_values = (0, 0, 0, 0)
            elif cls.__name__ == "Curve":
                parsed_values = (0.0, 0.0)
            else:
                parsed_values = ()

        # 객체 생성
        obj = cls(station, *parsed_values)
        return obj

    def parse_rail_components(self, components):
        rail_index, x, y, obj_index = 0, 0.0, 0.0, 0
        for i, val in enumerate(components):
            try:
                if i == 0:
                    rail_index = try_parse_int(val)
                elif i == 1:
                    x = try_parse_float(val)
                elif i == 2:
                    y = try_parse_float(val)
                elif i == 3:
                    obj_index = try_parse_int(val)
            except ValueError:
                print(f"ValueError: 줄 {self.linenumber} 열 {i} 파싱 실패: {val}")
        return rail_index, x, y, obj_index

    def parse_form_components(self, components):
        a, b, c, d = 0, 0, 0, 0
        for i, val in enumerate(components):
            try:
                if i == 0:
                    a = try_parse_int(val)
                elif i == 1:
                    b = try_parse_int(val)
                    if b == -1 or (isinstance(val, str) and val.strip().lower() == 'l'):
                        b = -1
                elif i == 2:
                    c = try_parse_int(val)
                elif i == 3:
                    d = try_parse_int(val)
            except ValueError:
                print(f"ValueError: 줄 {self.linenumber} 열 {i} 파싱 실패: {val}")
        return a, b, c, d

    def parse_curve_components(self, components):
        a, b = 0.0, 0.0
        for i, val in enumerate(components):
            try:
                if i == 0:
                    a = try_parse_float(val)
                elif i == 1:
                    b = try_parse_float(val)
            except ValueError:
                print(f"ValueError: 줄 {self.linenumber} 열 {i} 파싱 실패: {val}")
        return a, b
    #통합 처리 메소드
    def process_lines_to_alginment_data(self, lines):
        # 기존 변수 초기화
        alignment = None
        alignments = []
        station_list = []
        forms = []
        formdata = None
        self.lines = lines
        curve_list_for_main = []  # 자선에 넣을 curve 리스트 따로 저장


        line_type_map = {
            '.rail': (self.parse_rail_components, Rail),
            '.curve': (self.parse_curve_components, Curve),
            '.form': (self.parse_form_components, Form)
        }

        for linenumber, line in enumerate(self.lines, start=1):
            #linenumber와 line 상태저장
            self.linenumber = linenumber
            self.line = line.strip()

            if not self.line:
                continue

            if line.startswith(',;'):
                # 기존 alignment 저장
                if alignment and alignment.raildata:
                    alignments.append(alignment)

                # 새 배선 생성
                current_rail_name = line.split(';', 1)[1].strip()
                from alignment_geometry.alignment import Alignment
                alignment = Alignment(current_rail_name)

                if formdata and formdata.formdata:
                    forms.append(formdata)
                from alignment_geometry.formdata import FormData
                formdata = FormData(current_rail_name)

                continue

            line_lower = self.line.lower()
            matched = False
            for key, (parse_func, cls) in line_type_map.items():
                if key == '.rail' and key in line_lower and '.railtype' not in line_lower:
                    matched = True
                elif key != '.rail' and key in line_lower:
                    matched = True
                if matched:
                    obj = self.parse_line(parse_func, cls)
                    if obj:

                        if isinstance(obj, Rail):
                            station_list.append(obj.station)
                            if alignment:
                                alignment.raildata.append(obj)
                                alignment.index = obj.railindex
                        elif isinstance(obj, Form) and formdata:
                            formdata.formdata.append(obj)
                        elif isinstance(obj, Curve):
                            curve_list_for_main.append(obj)
                    break  # 한 줄은 한 타입만

        # 마지막 배선, 폼 데이터 누락 방지
        if alignment and alignment.raildata:
            alignments.append(alignment)
        if formdata and formdata.formdata:
            forms.append(formdata)

        return alignments, forms ,curve_list_for_main,  min(station_list), max(station_list)
