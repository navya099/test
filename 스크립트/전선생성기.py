from csvobject import CSVObject
from 텍스트치환 import read_lines, replace_csv_file_length_text, save_file
import os
import numpy as np
from 카테너리전선시각화 import sag_parabola

def main():
    # 원본 파일 경로 리스트 만들기
    namelist = ['FPW', '급전선', '무효용조가선', '무효용전차선']
    #소스 파일
    input_files = [
        rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\{name}_base.csv"
        for name in namelist
    ]
    #실행
    for input_file in input_files:
        lines = read_lines(input_file)
        base_name = os.path.basename(input_file).split("_")[0]  # FPW, 급전선 등
        result = []
        for number in range(1, 64):
            f = sag_parabola(L=number, w=1.5, T=800)
            count = 10
            seg_length = number / count
            xs = np.linspace(0, number, count)
            ys = [-4 * f / (number ** 2) * x * (number - x) for x in xs]

            lines_out = []
            for i in range(len(xs) - 1):
                x1, y1 = xs[i], ys[i]
                x2, y2 = xs[i + 1], ys[i + 1]

                dx = x2 - x1
                dy = y2 - y1
                import math
                angle = math.degrees(math.atan2(dy, dx))

                replaced_lines = replace_csv_file_length_text(
                    old_text='13',
                    new_text=str(seg_length),
                    lines=lines
                )
                csv = CSVObject(replaced_lines)
                csv.set_lines(csv.translate(dx=0, dy=y1, dz=x1))
                csv.rotate(axis_x=0, axis_y=0, axis_z=1, angle=angle)

                # 변환된 줄만 누적
                lines_out.extend(csv.lines)

            output_file = rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\{base_name}_{number}m.csv"
            
            save_file(output_file, lines_out)

if __name__ == "__main__":
    main()
