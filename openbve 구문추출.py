from tkinter import filedialog, ttk
import os
import re

class CsvRouteParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.context = ParseContext()
        self.preprocessor = Preprocessor()
        self.result = []

    def parse(self):
        lines = self.preprocessor.preprocess(self.filepath)
        for lineno, line in enumerate(lines):
            expressions = tokenize_line(line)
            for expr in expressions:
                parsed_expr = self._parse_expression(expr, lineno)
                if parsed_expr:
                    self.result.append(parsed_expr)

    def _parse_expression(self, expr, lineno):
        if not expr.parts:
            #print(f"[Line {lineno}] Empty expression: {expr.raw}")
            return None

        name, *args = expr.parts
        full_name = self.context.resolve_name(name)

        # track position 추출 (예: '62167.956,.CURVE -35969.277')
        trackpos_match = re.match(r"^\s*(\d+(?:\.\d+)?),", expr.raw)
        trackpos = float(trackpos_match.group(1)) if trackpos_match else None

        expression = Expression(full_name, args, lineno, raw=expr.raw, trackpos=trackpos)

        if full_name in COMMANDS:
            try:
                result = COMMANDS[full_name](args)
                expression.value = result
            except Exception as e:
                print(f"[Line {lineno}] Error parsing {full_name} with args {args}: {e}")
                expression.value = None

        return expression


class ParseContext:
    def __init__(self):
        self.current_prefix = None  # e.g., 'Route', 'Track'

    def set_prefix(self, prefix):
        self.current_prefix = prefix

    def resolve_name(self, name):
        if name.startswith(".") and self.current_prefix:
            return f"{self.current_prefix}{name}"
        return name

def tokenize_line(line: str):
    line = line.strip()
    if not line or line.startswith(";"):
        return []

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
        self.includes = set()

    def preprocess(self, filepath):
        return self._read_with_includes(filepath)

    def _read_with_includes(self, filepath, base_offset=0.0):
        lines = []
        try:
            with open(filepath, encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("$Include"):
                        include_path = os.path.join(os.path.dirname(filepath), extract_include_path(line))
                        included_lines = self._read_with_includes(include_path)
                        lines.extend(included_lines)
                    else:
                        lines.append(line)
        except Exception as ex:
            print(f'{ex}')
            return []
        return lines

def extract_include_path(line):
    # $Include(filename.txt) 형식 또는 $Include filename.txt 형식 모두 처리
    line = line.strip()
    
    # 괄호형 처리: $Include(filename.txt)
    match = re.match(r'\$Include\s*\(([^)]+)\)', line)
    if match:
        return match.group(1).strip().strip('"')

    # 공백형 처리: $Include filename.txt
    parts = line.split(maxsplit=1)
    if len(parts) == 2:
        return parts[1].strip().strip('"')

    raise ValueError(f"Invalid $Include syntax: {line}")

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

COMMANDS = {
    'Route.Gauge': lambda args: float(args[0]),
    'Route.Timetable': lambda args: str(args[0]),
    '.CURVE': parse_curve,  # 접두사 없는 경우
    'Track.Curve': parse_curve  # 접두사 있는 경우
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
        for expr in parser.result:
            if expr.name.endswith(".PITCH"):
                print(f"{expr.lineno:5}: {expr.name:<15} {expr.args} => {expr.value} @ {expr.trackpos}")
