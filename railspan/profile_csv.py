"""Read station/elevation CSV for longitudinal and ground profiles."""
import csv
import io

from .engine import validate_profile

COLUMNS = ("station", "elevation")
EXAMPLES = {
    "/profile-example.csv": [(0, 15), (55, 16.5), (110, 15)],
    "/ground-example.csv": [(0, 2), (55, -1), (110, 3)],
}


def profile_example(points):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(COLUMNS)
    writer.writerows(points)
    return output.getvalue().encode("utf-8-sig")


def read_profile(payload):
    try:
        stream = io.StringIO(payload.decode("utf-8-sig"), newline="")
    except UnicodeError as error:
        raise ValueError("CSV 파일을 UTF-8로 저장하세요.") from error
    reader = csv.reader(stream, strict=True)
    points = []
    try:
        header = tuple(value.strip() for value in next(reader, []))
        if len(header) != len(COLUMNS) or set(header) != set(COLUMNS):
            raise ValueError("CSV 열 이름을 station, elevation으로 입력하세요.")
        for row in reader:
            if not row or (len(row) == 1 and not row[0].strip()):
                continue
            if len(row) != len(header):
                raise ValueError(f"CSV {reader.line_num}행에 측점과 표고를 입력하세요.")
            fields = dict(zip(header, row))
            try:
                points.append([float(fields[key]) for key in COLUMNS])
            except ValueError as error:
                raise ValueError(f"CSV {reader.line_num}행의 측점과 표고를 숫자로 입력하세요.") from error
            if len(points) > 100:
                raise ValueError("CSV는 최대 100개의 측점까지 가져올 수 있습니다.")
    except csv.Error as error:
        raise ValueError(f"CSV {reader.line_num}행의 형식을 확인하세요.") from error
    if len(points) < 2:
        raise ValueError("CSV에 측점을 2개 이상 입력하세요.")
    return validate_profile(points, "CSV 데이터", -1000, 8150)
