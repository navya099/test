from BVECSVObejct.csvobjectmodifyer import CSVObject
from 텍스트치환 import read_lines, replace_csv_file_length_text, save_file
import os
import numpy as np
from 카테너리전선시각화 import sag_parabola
import math

def main():
    # 원본 파일 경로 리스트 만들기
    namelist = ['FPW', '급전선', '무효용조가선', '무효용전차선']
    #소스 파일
    input_files = [
        rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\{name}.csv"
        for name in namelist
    ]
    #실행
    for name, input_file in zip(namelist,input_files):
        lines = read_lines(input_file)
        for number in range(1, 64):
            if name in ["무효용조가선", "무효용전차선"]:  # 이도 없는 전선
                f = 0.0
                count = 2
            else:
                f = sag_parabola(L=number, w=1.5, T=800)
                count = 20
            xs = np.linspace(0, number, count)
            ys = [-4 * f / (number ** 2) * x * (number - x) for x in xs]

            lines_out = []
            for i in range(len(xs) - 1):
                x1, y1 = xs[i], ys[i]
                x2, y2 = xs[i + 1], ys[i + 1]

                dz = x2 - x1
                dy = y2 - y1
                seg_length = math.sqrt(dz ** 2 + dy ** 2)


                angle = math.degrees(math.atan2(-dy, dz))
                # 🔍 디버그 출력
                '''
                print(f"[DEBUG] seg {i + 1}: x1={x1:.3f}, y1={y1:.6f}, x2={x2:.3f}, y2={y2:.6f}, "
                      f"dz={dz:.3f}, dy={dy:.6f}, angle={angle:.3f}")
                '''

                replaced_lines = replace_csv_file_length_text(
                    old_text='13.0',
                    new_text=str(seg_length),
                    lines=lines
                )
                csv = CSVObject(replaced_lines)

                csv.rotate(axis_x=1, axis_y=0, axis_z=0, angle=angle)
                csv.translate(dx=0, dy=y1, dz=x1)
                '''
                # 🔍 최종 좌표 디버그 출력
                for line in csv.lines:
                    if line.strip().startswith("AddVertex"):
                        parts = line.strip().split(',')
                        vx, vy, vz = float(parts[1]), float(parts[2]), float(parts[3])
                        print(f"    [FINAL] seg {i + 1}: vx={vx:.3f}, vy={vy:.6f}, vz={vz:.3f}")
                '''
                # 변환된 줄만 누적
                lines_out.extend(csv.lines)

            output_file = rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\{name}_{number}m.csv"
            
            save_file(output_file, lines_out)

if __name__ == "__main__":
    main()
