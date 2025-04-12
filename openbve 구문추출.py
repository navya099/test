from tkinter import filedialog, ttk
import os
import re
import chardet
from dataclasses import dataclass
import math

def detect_encoding(path):
    # 파일을 열어 일부를 읽어서 인코딩을 감지합니다
    with open(path, 'rb') as file:
        raw_data = file.read(10000)  # 처음 10000 바이트를 읽어봄
        result = chardet.detect(raw_data)  # 인코딩 탐지
        return result['encoding']

class CurrentRoute:
    def __init__(self):
        self.Options = Options()
        self.Route = Route()
        self.Track = Track()

class Options:
    def __init__(self):
        self.ObjectVisibility = 1
        self.Blocklength = 25

class Route:
    def __init__(self):
        self.comment = ''
        self.Elevation = 0.0
        self.PositionX = 0.0
        self.PositionY = 0.0
        self.Direction = 0.0
        self.timetable = ''

class Track:
    def __init__(self):
        self.Blocks = []

class Curve:
    def __init__(self):
        self.radius = 0.0
        self.cant = 0.0

class Pitch:
    def __init__(self):
        self.pitch = 0.0

class Rail:
    def __init__(self):
        self.index = 0
        self.x = 0.0
        self.y = 0.0
        self.objidx = 0

class Block:
    def __init__(self):
        self.index = 0
        self.TrackPosition = 0.0
        self.Curve = Curve()
        self.Pitch = Pitch()
        self.Rail = Rail()

@dataclass
class ParsedLine:
    global_lineno: int
    local_lineno: int
    filepath: str
    content: str
    offset: float

class CsvRouteParser:
    def __init__(self, filepath):
        self.CurrentRoute = CurrentRoute()
        self.filepath = filepath
        self.context = ParseContext()
        self.preprocessor = Preprocessor()
        self.result = []
        self.lasttrackposition = None

    def parse(self):
        lines = self.preprocessor.preprocess(self.filepath).lines
        for i ,line in enumerate(lines):
            expressions = tokenize_line(line.content)
            for expr in expressions:
                parsed_expr = self._parse_expression(expr, line.global_lineno)
                if parsed_expr:
                    self.result.append(parsed_expr)

    def _parse_expression(self, expr, lineno):
        if not expr.parts:
            #print(f"[Line {lineno}] Empty expression: {expr.raw}")
            return None

        name, *args = expr.parts
        full_name, option = self.context.resolve_name(name, *args)


        # track position 추출 (예: '62167.956,.CURVE -35969.277')
        if self.context.current_prefix == 'Options':
            if option.lower() == 'objectvisibility':

                self.CurrentRoute.Options.ObjectVisibility = option
            elif option.lower() == 'blocklength':
                self.CurrentRoute.Options.Blocklength = option
            return False
        elif self.context.current_prefix == 'Route':
            if name.lower() == '.comment':
                self.CurrentRoute.Route.comment = " ".join(args)
            elif name.lower() == '.elevation':
                self.CurrentRoute.Route.Elevation = args[0]
            elif name.lower() == '.positionx':
                self.CurrentRoute.Route.PositionX = args[0]
            elif name.lower() == '.positiony':
                self.CurrentRoute.Route.PositionY = args[0]
            elif name.lower() == '.direction':
                self.CurrentRoute.Route.Direction = args[0]
            return False

        elif self.context.current_prefix == 'Train':
            return False
        elif self.context.current_prefix == 'Structure':
            return False

        elif self.context.current_prefix == 'Track':
            if isinstance(full_name, float):  # 트랙포지션인경우
                self.lasttrackposition = full_name
                return False
            else:
                if not full_name.lower() == 'track':
                    expression = Expression(full_name, args, lineno, raw=expr.raw, trackpos=self.lasttrackposition)
                    if full_name in COMMANDS:
                        try:
                            result = COMMANDS[full_name](args)
                            expression.value = result
                        except Exception as e:
                            print(f"[Line {lineno}] Error parsing {full_name} with args {args}: {e}")
                            expression.value = None

                    else:
                        return False
                else:
                    return False
        else:
            return False
        return expression

class ApplyRouteData:
    def __init__(self, currentroute, expr):
        self.currentroute = currentroute
        self.expr = expr

    def applyroutedata(self):
        expr = sorted(self.expr, key=lambda e: e.trackpos)
        currentroute = self.currentroute

        lastpos = expr[-1].trackpos
        lastindex = get_block_index(lastpos)

        # 필요한 만큼 Block 생성
        while len(currentroute.Track.Blocks) <= lastindex:
            currentroute.Track.Blocks.append(Block())

        # Step 1: Curve 값 미리 저장
        curve_data = {}  # block_index: (radius, cant)
        for item in expr:
            if item.name == 'Track.Curve':
                index = get_block_index(item.trackpos)
                curve_data[index] = (item.value['radius'], item.value['cant'])

        pitch_data = {}  # block_index: (radius, cant)
        for item in expr:
            if item.name == 'Track.Pitch':
                index = get_block_index(item.trackpos)
                pitch_data[index] = (item.value['pitch'])
        # Step 2: Block에 값 적용
        lastradius = 0.0
        lastcant = 0.0
        lastpitch = 0.0
        for i in range(len(currentroute.Track.Blocks)):
            current_trackposition = i * 25
            currentroute.Track.Blocks[i].TrackPosition = current_trackposition

            if i in curve_data:
                lastradius, lastcant = curve_data[i]
            if i in pitch_data:
                lastpitch = pitch_data[i]

            currentroute.Track.Blocks[i].Curve.radius = lastradius
            currentroute.Track.Blocks[i].Curve.cant = lastcant
            currentroute.Track.Blocks[i].Pitch.pitch = lastpitch


def get_block_index(current_track_position, block_interval=25):
    """현재 트랙 위치를 블록 인덱스로 변환"""

    return math.floor(current_track_position / block_interval + 0.001)



class ParseContext:
    def __init__(self):
        self.current_prefix = None  # e.g., 'Route', 'Track'

    def set_prefix(self, prefix):
        self.current_prefix = prefix

    def _is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def resolve_name(self, name, *args):
        option = ''
        name = name.lower()  # 전부 소문자로
        if name in ['route', 'train', 'structure', 'track']:
            self.current_prefix = name.capitalize() # 첫글자만 대문자로
            option = ''
        elif name == 'with':
            for arg in args:
                arg = arg.lower()
                if arg in ['route', 'train', 'structure', 'track']:
                    option = ''
                    name = arg.capitalize()
                    self.current_prefix = name
        elif name.startswith('options'):
            parts = name.split('.')

            name, option = parts
            name = name.capitalize()
            option = option.capitalize()
            self.current_prefix = name.capitalize()

        elif name == '':
            name = ''
            option = ''
        elif self._is_float(name):
            trackposition = float(name)
            name = trackposition
            option = ''
        else:
            name = capitalize_command(name)
            name = f'{self.current_prefix}{name}'
            option = ''
        return name, option

def capitalize_command(cmd: str) -> str:
    if cmd.startswith('.') and len(cmd) > 1:
        return cmd[0] + cmd[1:].capitalize()
    return cmd

def tokenize_line(line: str):
    line = line.strip()
    match = re.match(r'^(\d+)', line)
    if not line or line.startswith(";"):  # 주석
        return []
    if line.lower().startswith("with"):  # current_prefix
        tokens = line.split(",")

    elif line.lower().startswith("options"):
        tokens = line.split(",")
    else:
        tokens = line.split(",")
    return [ExpressionToken(token.strip()) for token in tokens]

class ExpressionToken:
    def __init__(self, raw):
        self.raw = raw
        self.parts = self._split_parts(raw)

    def _split_parts(self, raw):
        raw = raw.strip()
        # 괄호형: Track.Curve(0.5;100)
        if "(" in raw and raw.endswith(")"):
            cmd, args = raw[:-1].split("(", 1)
            return [cmd] + [arg.strip() for arg in args.split(";") if arg.strip()]
        # 일반형: .CURVE -3550;0;
        elif ";" in raw:
            parts = raw.split(None, 1)  # 명령어와 인수 구분
            if len(parts) == 2:
                cmd, args = parts
                return [cmd] + [arg.strip() for arg in args.split(";") if arg.strip()]
            else:
                return [raw]
        else:
            return raw.split()



class Preprocessor:
    def __init__(self):
        self.global_lineno = 0
        self.includes = set()
        self.lines = []

    def preprocess(self, filepath):
        self.lines = self._read_with_includes(filepath)
        return self

    def _read_with_includes(self, filepath):
        collected_lines = []
        try:
            encoding = detect_encoding(filepath)
            with open(filepath, encoding=encoding) as f:
                for local_lineno, line in enumerate(f, start=1):
                    line = line.strip()
                    self.global_lineno += 1

                    if line.lower().startswith("$include"):
                        include_path, offset = extract_include_path(line)
                        full_include_path = os.path.join(os.path.dirname(filepath), include_path)
                        included_lines = self._read_with_includes(full_include_path)
                        collected_lines.extend(included_lines)
                    else:
                        offset = 0
                        collected_lines.append(
                            ParsedLine(self.global_lineno, local_lineno, filepath, line, offset)
                        )
        except Exception as ex:
            print(f'[Preprocessor Error] {ex}')
        return collected_lines


def extract_include_path(line):
    """
    $Include(filename.txt), $Include filename.txt,
    $Include(filename.txt:offset), $Include filename.txt:offset
    모든 형식을 지원함.
    반환값: (파일 경로, offset: float 또는 0.0)
    """
    line = line.strip()
    offset = 0.0

    # 괄호형 처리: $Include(filename.txt:offset)
    match = re.match(r'\$Include\s*\(([^)]+)\)', line, re.IGNORECASE)
    if match:
        content = match.group(1).strip().strip('"')
    else:
        # 공백형 처리: $Include filename.txt[:offset]
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Invalid $Include syntax: {line}")
        content = parts[1].strip().strip('"')

    # 파일명과 offset 분리
    if ':' in content:
        filename, offset_str = content.split(':', 1)
        try:
            offset = float(offset_str)
        except ValueError:
            raise ValueError(f"Invalid offset value: {offset_str}")
        return filename.strip(), offset
    else:
        return content.strip(), 0.0


from dataclasses import dataclass

@dataclass
class Expression:
    name: str              # 명령어 전체 이름 e.g., Route.Gauge
    args: list[str]        # 인수들 e.g., ['1435']
    lineno: int            # 원본 줄 번호
    raw: str = ""          # 원본 텍스트 (선택적)
    trackpos: float = None # 트랙 상 위치 (선택적)
    value: any = None      # 명령어 처리 결과


def parse_curve(args):
    try:
        radius = float(args[0])
        cant = float(args[1]) if len(args) > 1 else 0.0
        return {"radius": radius, "cant": cant}
    except Exception as e:
        raise ValueError(f"Invalid .CURVE args: {args}")

def parse_pitch(args):
    try:
        pitch = float(args[0])
        return {"pitch": pitch}
    except Exception as e:
        raise ValueError(f"Invalid .pitch args: {args}")

def parse_rail(args):
    try:
        railindex = int(args[0])
        xoffset = float(args[1]) if len(args) > 1 else 0.0
        yoffset = float(args[2]) if len(args) > 2 else 0.0
        object_index = int(args[3]) if len(args) > 3 else 0
        return {"railindex": railindex, "xoffset": xoffset, "yoffset": yoffset, "object_index": object_index}

    except Exception as e:
        raise ValueError(f"Invalid .rail args: {args}")


def parse_freeobj(args):
    try:
        railindex = int(args[0])
        freeobj_index = int(args[1]) if len(args) > 1 else 0
        xoffset = float(args[1]) if len(args) > 1 else 0.0
        yoffset = float(args[2]) if len(args) > 2 else 0.0
        yaw = float(args[3]) if len(args) > 2 else 0.0
        pitch = float(args[4]) if len(args) > 3 else 0.0
        roll = float(args[5]) if len(args) > 4 else 0.0
        return {'railindex': railindex, 'freeobj_index':freeobj_index, 'xoffset': xoffset,
                'yoffset': yoffset, 'yaw': yaw, 'pitch': pitch, 'roll': roll }


    except Exception as e:
        raise ValueError(f"Invalid freeobj args: {args}")
COMMANDS = {
    'Route.Gauge': lambda args: float(args[0]),
    'Route.Timetable': lambda args: str(args[0]),
    'Track.Curve': parse_curve,  # 접두사 있는 경우
    'Track.Pitch': parse_pitch, # 접두사 없는 경우
    'Track.Freeobj': parse_freeobj,
    'Track.Rail': parse_rail
}

#파일 읽기 함수
def read_file():
    global lines
     # Hide the main window
    file_path = filedialog.askopenfilename()  # Open file dialog
    return file_path

if __name__ == "__main__":
    file_path = read_file()
    if file_path:
        parser = CsvRouteParser(file_path)
        parser.parse()
        applyroutedata = ApplyRouteData(parser.CurrentRoute, parser.result)
        applyroutedata.applyroutedata()
        with open('c:/temp/curve_info.txt', 'w' ,encoding='utf-8') as f:
            for i in range(len(applyroutedata.currentroute.Track.Blocks)-1):
                f.write(f'{applyroutedata.currentroute.Track.Blocks[i].TrackPosition},')
                f.write(f'{applyroutedata.currentroute.Track.Blocks[i].Curve.radius},')
                f.write(f'{applyroutedata.currentroute.Track.Blocks[i].Curve.cant}\n')
        with open('c:/temp/pitch_info.txt', 'w' ,encoding='utf-8') as f:
            for i in range(len(applyroutedata.currentroute.Track.Blocks)-1):
                f.write(f'{applyroutedata.currentroute.Track.Blocks[i].TrackPosition},')
                f.write(f'{applyroutedata.currentroute.Track.Blocks[i].Pitch.pitch}\n')