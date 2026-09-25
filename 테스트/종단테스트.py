
import csv
from tkinter.filedialog import askopenfilename

# 동일 구배 병합 여부
MERGE_SEGMENTS = False   # True: 병합 / False: 병합 안 함
INPUT = askopenfilename(title="리습에서 추출한 CSV 선택")
if not INPUT:
    raise FileNotFoundError("대상 파일을 찾을 수 없습니다")
OUTPUT = "c:/temp/profile_gradients.csv"
SEGMENTS = "c:/temp/gradient_segments.csv"
OUTPUTBVE = "c:/temp/profile_gradients_BVE.csv"
# 구배가 같은 것으로 판단할 허용 오차 (‰)
TOLERANCE = 0.01

# CSV 읽기
with open(INPUT, encoding="utf-8-sig", newline="") as f:
    rows = [
        (float(r["Station"]), float(r["Elevation"]))
        for r in csv.DictReader(f)
    ]

rows.sort(key=lambda x: x[0])

# 측점별 구배 계산
results = []

for i in range(1, len(rows)):
    s1, e1 = rows[i - 1]
    s2, e2 = rows[i]

    if s2 <= s1:
        raise ValueError("중복 또는 잘못된 측점이 있습니다.")

    gradient = (e2 - e1) / (s2 - s1) * 1000

    results.append({
        "Start": s1,
        "End": s2,
        "Elevation": e2,
        "Gradient": gradient
    })


# 구배 구간 생성
segments = []

if MERGE_SEGMENTS:
    # 동일 구배 구간 병합
    for r in results:
        if (
            segments
            and abs(
                segments[-1]["Gradient"] - r["Gradient"]
            ) <= TOLERANCE
        ):
            seg = segments[-1]
            seg["End"] = r["End"]
            seg["EndElevation"] = r["Elevation"]

            seg["Gradient"] = (
                (seg["EndElevation"] - seg["StartElevation"])
                / (seg["End"] - seg["Start"]) * 1000
            )
        else:
            start_elevation = (
                rows[0][1] if not segments
                else segments[-1]["EndElevation"]
            )

            segments.append({
                "Start": r["Start"],
                "End": r["End"],
                "StartElevation": start_elevation,
                "EndElevation": r["Elevation"],
                "Gradient": r["Gradient"]
            })

else:
    # 병합하지 않고 모든 측점별 구배 출력
    for i, r in enumerate(results):
        segments.append({
            "Start": r["Start"],
            "End": r["End"],
            "StartElevation": rows[i][1],
            "EndElevation": r["Elevation"],
            "Gradient": r["Gradient"]
        })

# CSV 출력
def save_csv(path, data):
    if not data:
        return

    with open(path, "w", encoding="utf-8-sig",
              newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(data[0].keys())
        )
        writer.writeheader()
        writer.writerows(data)

save_csv(OUTPUT, results)
save_csv(SEGMENTS, segments)

print(f"측점별 구배: {OUTPUT}")
print(f"병합된 구배 구간: {SEGMENTS}")

for seg in segments:
    print(
        f'{seg["Start"]:.1f} ~ {seg["End"]:.1f}m | '
        f'{seg["Gradient"]:+.3f}‰'
    )

with open(OUTPUTBVE, "w", encoding="utf-8-sig", newline="") as f:
    for seg in segments:
        station = seg["Start"]
        gradient = seg["Gradient"]

        # 부동소수점 오차에 따른 -0.000 방지
        if abs(gradient) < 0.0005:
            gradient = 0.0

        f.write(
            f"{station:.1f},.pitch {gradient:.3f};\n"
        )