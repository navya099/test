"""Read numeric CSV used for Railspan's alignment inputs."""
import csv
import io

from .engine import validate_plan, validate_profile

PROFILE_COLUMNS = ("station", "elevation")
CANT_COLUMNS = ("station", "cant_mm")
PLAN_COLUMNS = ("end_station", "start_radius", "end_radius")
EXAMPLES = {
    "/profile-example.csv": (PROFILE_COLUMNS, [(0, 15), (55, 16.5), (110, 15)]),
    "/ground-example.csv": (PROFILE_COLUMNS, [(0, 2), (55, -1), (110, 3)]),
    "/plan-example.csv": (PLAN_COLUMNS, [(20, 0, ""), (40, 0, -250), (75, -250, ""),
                                        (95, -250, 0), (110, 0, "")]),
    "/cant-example.csv": (CANT_COLUMNS, [(0, 0), (20, 0), (40, 120), (75, 120), (95, 0), (110, 0)]),
}


def alignment_example(columns, points):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(points)
    return output.getvalue().encode("utf-8-sig")


def read_points(payload, required, optional=()):
    try:
        stream = io.StringIO(payload.decode("utf-8-sig"), newline="")
    except UnicodeError as error:
        raise ValueError("CSV 파일을 UTF-8로 저장하세요.") from error
    reader = csv.reader(stream, strict=True)
    points = []
    try:
        header = tuple(value.strip() for value in next(reader, []))
        columns = set(header)
        if len(header) != len(columns) or not set(required) <= columns <= set(required + optional):
            raise ValueError(f"CSV 열 이름을 예제와 맞춰 주세요: {', '.join(required + optional)}")
        for row in reader:
            if not row or (len(row) == 1 and not row[0].strip()):
                continue
            if len(row) != len(header):
                raise ValueError(f"CSV {reader.line_num}행의 열 수를 확인하세요.")
            fields = dict(zip(header, row))
            try:
                values = [float(fields[key]) for key in required]
                values.extend(float(fields[key]) for key in optional if fields.get(key, "").strip())
                points.append(values)
            except ValueError as error:
                raise ValueError(f"CSV {reader.line_num}행의 값을 숫자로 입력하세요.") from error
            if len(points) > 100:
                raise ValueError("CSV는 최대 100행까지 가져올 수 있습니다.")
    except csv.Error as error:
        raise ValueError(f"CSV {reader.line_num}행의 형식을 확인하세요.") from error
    return points


def read_station_profile(payload, columns, label, minimum, maximum, **options):
    points = read_points(payload, columns)
    if len(points) < 2:
        raise ValueError("CSV에 측점을 2개 이상 입력하세요.")
    return validate_profile(points, label, minimum, maximum, **options)


def read_profile(payload):
    return read_station_profile(payload, PROFILE_COLUMNS, "CSV 데이터", -1000, 8150)


def read_cant(payload):
    return read_station_profile(payload, CANT_COLUMNS, "측점별 캔트", 0, 200, value_label="캔트(mm)")


def read_plan(payload):
    rows = read_points(payload, PLAN_COLUMNS[:2], PLAN_COLUMNS[2:])
    if not rows:
        raise ValueError("CSV에 평면 선형 구간을 1개 이상 입력하세요.")
    return validate_plan(rows)
