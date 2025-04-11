import os
import re
import csv
from dataclasses import dataclass
from abc import ABC
from typing import Optional, List, Union
from tkinter import filedialog, ttk

class CurrentRoute:
    def __init__(self):
        self.Options = Options()
        self.WithRoute = WithRoute()
        self.WithTrain = WithTrain()
        self.WithStructure = WithStructure()
        self.WithTrack = WithTrack()
        
@dataclass
class WithRoute:
    comment: str = ''
    Elevation: float = 0.0
    timetable: str = ''
    PositionX: float = 0.0
    PositionY: float = 0.0
    Direction: float = 0.0
    
@dataclass
class Options:
    ObjectVisibility: int = 0

@dataclass
class WithTrain:
    command: str = ''
    arg: int = 0
    value: int = 0

@dataclass
class WithStructure:
    command: str = ''
    arg1: int = 0
    arg2: int = 0
    value: str = ''


class Block:
    def __init__(self):
        self.index = 0
        self.curve = CurveCommand()
        self.rail = RailCommand()
        self.pitch = PitchCommand()
        
class WithTrack:
    def __init__(self):
        self.trackposition = 0.0
        block = Block()
        self.Blocks = [block]
    


        
# ----- Command 클래스 정의 -----
@dataclass(kw_only=True)
class CommandBase(ABC):
    index: Optional[str] = 0

@dataclass
class CurveCommand(CommandBase):
    radius: float = 0.0
    cant: float = 0.0

@dataclass
class RailCommand(CommandBase):
    railnumber: int = 0
    x: float = 0.0
    y: float = 0.0
    onjindex: int = 0

@dataclass
class PitchCommand(CommandBase):
    pitch: float = 0.0

COMMAND_CLASSES = {
    'curve': (CurveCommand, [float, float]),
    'rail': (RailCommand, [int, float, float, int]),
    'pitch': (PitchCommand, [float]),
}

# ----- 유틸리티 클래스: 라인 파서 -----
class CommandExtractor:
    def __init__(self):
        self.CurrentRoute = CurrentRoute()
    
    @staticmethod
    def parse_and_cast_args(args: List[str], types: List[type]) -> Union[List, None]:
        try:
            return [t(a) for t, a in zip(types, args)]
        except Exception:
            return None

    def parse_line(self, line: str):
        currentroute = self.CurrentRoute
        line = line.strip()
        print(f'currentline: {line}')
        if not line or line.startswith(';'):
            return

        level = 0
        section= None
        command = None
        prefix = None
        #문자열을 순회하면서 조회
        for i, t in enumerate(line):
            #시작문자가 숫자인경우
            print(f'current char : {t}')
            try:
                float(t)
                level += 1
            #시작문자가 문자인경우
            except:
                if t.lower().startswith('o'):
                    command = line.split('.')[0]
                    if command.lower() == 'options':
                        atribute = line.split('.')[1].split(' ')[0]
                        value = line.split('.')[1].split(' ')[1]
                        currentroute.Options.ObjectVisibility = value
                        break    
                    else:
                        print(f'invalid Options at line {i}')
                elif t.lower().startswith('w'):
                    if line[:4].lower() == 'With'.lower():
                        section = line.split(' ')[1]
                        break
                    else:
                        print(f'invalid With at line {i}')
                elif t.lower().startswith('.'):
                    prefix = line.split(' ')[0][1:]
                    string = line.split(' ')[1]
                    if prefix.lower() == 'comment':
                        break
                    elif prefix.lower() == 'elevation':
                        break
                    elif prefix.lower() == 'timetable':
                        break
                    elif prefix.lower() == 'positionx':
                        break
                    elif prefix.lower() == 'positiony':
                        break
                    elif prefix.lower() == 'direction':
                        break
                    else:
                      print(f'invalid comment at line {i}')
                      
        if section == 'Route':
            if prefix == 'comment':
                currentroute.WithRoute.comment = string
            elif prefix == 'Elevation':
                currentroute.WithRoute.Elevation = float(string)
            elif prefix == 'timetable':
                currentroute.WithRoute.timetable = string
            elif prefix == 'PositionX':
                currentroute.WithRoute.PositionX = float(string)
            elif prefix == 'PositionY':
                currentroute.WithRoute.PositionX = float(string)
            elif prefix == 'Direction':
                currentroute.WithRoute.PositionX = float(string)
        elif section == 'Train':
            pass
        elif section == 'Structure':
            pass
        elif section == 'Track':
            # 전처리
            if command == '$Include':
                preprocessor = RoutePreprocessor(route_path)
                expanded_lines = preprocessor.expand_includes()
            elif command == 'trackposition':
                currentroute.WithTrack.PositionX
            i += 1
        if i ==10:
            raise Exception
            
# ----- 클래스: 라우트 전처리기 -----
class RoutePreprocessor:
    def __init__(self, main_file_path: str):
        self.main_file_path = main_file_path
        self.base_dir = os.path.dirname(main_file_path)

    def expand_includes(self) -> List[str]:
        output_lines = []
        current_line_number = 1

        with open(self.main_file_path, encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            stripped = line.strip()
            include_match = re.match(r"\$Include\((.+?)\)", stripped)

            output_lines.append(f"{current_line_number} {line.rstrip()}")
            current_line_number += 1

            if include_match:
                include_filename = include_match.group(1)
                include_path = os.path.join(self.base_dir, include_filename)

                if os.path.exists(include_path):
                    with open(include_path, encoding="utf-8") as inc:
                        include_lines = inc.readlines()

                    for inc_line in include_lines:
                        output_lines.append(f"{current_line_number} {inc_line.rstrip()}")
                        current_line_number += 1
                else:
                    output_lines.append(f"{current_line_number} ; ERROR: file not found {include_filename}")
                    current_line_number += 1

        return output_lines

#파일 읽기 함수
def read_file():
    global lines
     # Hide the main window
    file_path = filedialog.askopenfilename()  # Open file dialog
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    return file_path

# ----- 사용 예시 -----
if __name__ == "__main__":
    parser = CommandExtractor()
    # main route 파일
    route_path = read_file()
    output_curve_csv = r'c:\temp\curve.csv'

    # 라우트 전처리
    preprocessor = RoutePreprocessor(route_path)
    expanded_lines = preprocessor.expand_includes()

    # 커브 정보 추출
    curve_data = []
    for raw_line in expanded_lines:
        _, line = raw_line.split(" ", 1)
        result = parser.parse_line(line)
    '''
        if result and result['type'] == 'command' and result['command'] == 'curve':
            curve = result['data']
            curve_data.append([result['index'], curve.radius, curve.cant])
        
    # CSV 저장
    with open(output_curve_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Index', 'Radius', 'Cant'])
        writer.writerows(curve_data)
    '''
