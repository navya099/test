from 테스트.civil3d오차_1e9 import CivilDocument
golden_pah = r'c:/temp/dynamo_test/css.json'
doc = CivilDocument.from_golden_json(golden_pah)
align = doc.alignments[0]

# 단일 평가
x, y = align.point_location(1483.908215495, 0.0)

# 대량 벡터화 평가 (예: 100만 개)
import numpy as np, time
stations = np.linspace(0.0, align.ending_station, 1_000_000)
t0 = time.perf_counter()
xs, ys, azs = align.point_locations_many(stations)
print(f"1M points: {time.perf_counter()-t0:.2f}s")