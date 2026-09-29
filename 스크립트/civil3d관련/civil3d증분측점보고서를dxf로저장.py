from tkinter.filedialog import askopenfilename, askdirectory

import ezdxf


def main():
    filepath = None
    while True:
        try:
            filepath = askopenfilename(title="Civil3D 보고서 또는 AcadLisp CSV 선택")
            if not filepath:
                raise FileNotFoundError("대상 파일을 찾을 수 없습니다")

            # 파일 읽기
            from 테스트.bvecivil3d실제선형구현테스트 import read_civil3d_data
            chainages, coords, bearings, mode = read_civil3d_data(filepath)

            print(f"파일 읽기 성공: {filepath}, 모드={mode}")
            break

        except Exception as e:
            print(f"오류 발생: 파일: {filepath}는 {e}")
            print("올바른 Civil3D 보고서(.xls) 또는 AcadLisp CSV(.csv)를 선택하세요.")
    # 좌표계 변환 (Civil 좌표계 → 수학 좌표계)
    coords = [[y, x] for x, y in coords]

    #저장
    filepath_curve = askdirectory()
    if not filepath_curve:
        raise FileNotFoundError('저장 파일 경로가 선택되지 않았습니다.')

    # 곡선 결과 저장
    import os
    dxf_file = os.path.join(filepath_curve, '증분측점보고서.dxf')
    create_plan(chainages, coords, dxf_file)

def create_plan(chainages, coords, output_path):
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    # Create a 3D polyline
    plan_2d_name = "c3d"
    layer_color = 5
    plan_2d_layer = doc.layers.new(name=plan_2d_name, dxfattribs={'color': layer_color})
    msp.add_lwpolyline(coords, dxfattribs={'layer': plan_2d_name, 'const_width': 0})
    doc.saveas(output_path)

if __name__ == '__main__':
    main()