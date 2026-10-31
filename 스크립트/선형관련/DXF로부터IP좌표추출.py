from tkinter.filedialog import askopenfilename

import ezdxf

def read_dxf(file_path):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    coordinates = []

    for entity in msp.query("LWPOLYLINE"):
        for x, y, *_ in entity:
            coordinates.append((x, y))

    return coordinates

def main():
    #파일 읽기
    file_path = None
    file_path = askopenfilename(title='dxf파일 선택', filetypes=[("dxf 파일", "*.dxf")])
    if not file_path:
        raise FileNotFoundError('파일을 찾을수없습니다.')
    #좌표읽기
    coordinates = read_dxf(file_path)

    # 결과를 파일에 저장
    # 결과 저장
    from pathlib import Path
    output_path = Path(file_path).with_suffix(".txt")

    # TXT 저장
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for x, y in coordinates:
                f.write(f"{x:.3f},{y:.3f}\n")

        print(f"파일이 성공적으로 저장되었습니다: {output_path}")

    except Exception as e:
        print(f"파일 저장 실패: {e}")

if __name__ == '__main__':
    main()
