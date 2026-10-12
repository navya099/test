from tkinter import Label
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import ezdxf

def on_drop(event):
    # 드래그 앤 드롭된 파일 경로를 가져옵니다
    files = root.tk.splitlist(event.data)
    file_paths = [f for f in files if f.lower().endswith('.txt')]
    if not file_paths:
        label.config(text="txt 파일이 아닙니다.")
        return

    # 선택된 파일의 디렉토리 경로를 가져옵니다
    output_dir = os.path.dirname(file_paths[0])
    output_path = os.path.join(output_dir, "converted_dxf.dxf")

    # txt파일 파일열기
    points = txt_parsing(file_paths[0])

    #dxf content 작성
    create_polyline_dxf(points, output_path)
    # 결과를 파일에 저장
    try:
        label.config(text=f"파일이 성공적으로 저장되었습니다: {output_path}")
    except Exception as e:
        label.config(text=f"파일을 저장하는데 실패했습니다: {output_path} - {str(e)}")

def txt_parsing(file):
    points = []
    with open(file, 'r') as f:
        # txt 파일을 읽고 각 라인을 튜플로 묶기
        for line in f:
            x, y = map(float, line.split())
            points.append((x, y))
    return points


def create_polyline_dxf(points, output_path):
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    # Create a 3D polyline
    eg_profile_layer_name = 'GROUND_PROFILE'
    fg_profile_layer_name = 'PLAN_PROFILE'

    eg_profile_layer_color = 8
    fg_profile_layer_color = 1
    doc.layers.new(name=eg_profile_layer_name, dxfattribs={'color': eg_profile_layer_color})
    doc.layers.new(name=fg_profile_layer_name, dxfattribs={'color': fg_profile_layer_color})
    msp.add_lwpolyline(points, dxfattribs={'layer': eg_profile_layer_name, 'const_width': 0})
    doc.saveas(output_path)


# TkinterDnD 초기화
root = TkinterDnD.Tk()

# 레이블 생성
label = Label(root, text="파일을 여기로 드래그 앤 드롭하세요.")
label.pack()

# 드롭 이벤트 바인딩
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

# GUI 실행
root.mainloop()
