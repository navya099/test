import re
import pandas as pd

#bvefile = r'D:\BVE\루트\Railway\Route\옛 경춘선\교량.txt'
bvefile = r'D:\BVE\루트\Railway\Route\옛 경춘선\터널.txt'
with open(bvefile, "r", encoding="utf-8") as f:
    lines = f.readlines()

numbers = []
railtypes = []

for line in lines:
    line = line.strip()
    # 숫자만 있는 줄
    if re.match(r'^\d+$', line):
        numbers.append(int(line))
    # railtype 줄
    elif line.startswith(".railtype"):
        vals = line.split(";")
        # ".railtype 0;18;" → 두 번째 값이 railtype
        if len(vals) > 1 and vals[1].isdigit():
            railtypes.append(int(vals[1]))
        else:
            railtypes.append(0)

# 2개씩 묶기 (짝 안 맞으면 마지막은 버림)
pairs = []
for i in range(0, len(numbers) - 1, 2):
    pairs.append((numbers[i], numbers[i+1]))

# railtype 매칭 (없으면 0)
data = []
for i, (start, end) in enumerate(pairs):
    rail = railtypes[i] if i < len(railtypes) else 0
    data.append([start, end, rail])

# DataFrame 생성
df = pd.DataFrame(data, columns=["시작측점", "끝측점", "railtype"])

# 엑셀 저장


# 엑셀 저장
df.to_excel(r"c:/temp/구조물.xlsx", index=False)