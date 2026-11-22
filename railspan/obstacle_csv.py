"""Import and export axis-aligned obstacle envelopes in local metres."""
import csv
import io

from .engine import EXAMPLE, validate_obstacles

COLUMNS = ("name", "station_min", "offset_min", "elevation_min",
           "station_max", "offset_max", "elevation_max")
OPTIONAL_COLUMNS = ("category", "clearance_m", "clearance_mode")


def example_csv():
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(COLUMNS + OPTIONAL_COLUMNS)
    for obstacle in EXAMPLE["obstacles"]:
        writer.writerow([obstacle["name"], *obstacle["min"], *obstacle["max"],
                         obstacle.get("category", "other"), obstacle.get("clearance", ""),
                         obstacle.get("clearance_mode", "")])
    return stream.getvalue().encode("utf-8-sig")


def read_obstacles(payload):
    try:
        stream = io.StringIO(payload.decode("utf-8-sig"), newline="")
    except UnicodeError as error:
        raise ValueError("CSV 파일을 UTF-8로 저장하세요.") from error
    reader = csv.reader(stream, strict=True)
    obstacles = []
    try:
        header = tuple(value.strip() for value in next(reader, []))
        columns = set(header)
        if (len(header) != len(columns) or not set(COLUMNS) <= columns
                or not columns <= set(COLUMNS + OPTIONAL_COLUMNS)):
            raise ValueError("CSV 열 이름을 예제 CSV와 맞춰 주세요.")
        for row in reader:
            if not any(value.strip() for value in row):
                continue
            if len(row) != len(header):
                raise ValueError(f"CSV {reader.line_num}행의 열 수를 확인하세요.")
            fields = dict(zip(header, row))
            try:
                coordinates = [float(fields[key]) for key in COLUMNS[1:]]
                obstacle = {"name": fields["name"], "min": coordinates[:3], "max": coordinates[3:]}
                category = fields.get("category", "").strip()
                clearance = fields.get("clearance_m", "").strip()
                if category:
                    obstacle["category"] = category
                mode = fields.get("clearance_mode", "").strip()
                if mode:
                    obstacle["clearance_mode"] = mode
                if clearance:
                    try:
                        obstacle["clearance"] = float(clearance)
                    except ValueError as error:
                        raise ValueError("clearance_m은 숫자로 입력하세요.") from error
                obstacles.extend(validate_obstacles([obstacle]))
            except ValueError as error:
                raise ValueError(f"CSV {reader.line_num}행: {error}") from error
            if len(obstacles) > 100:
                raise ValueError("지장물 CSV는 최대 100개까지 가져올 수 있습니다.")
    except csv.Error as error:
        raise ValueError(f"CSV {reader.line_num}행의 형식을 확인하세요.") from error
    return obstacles
