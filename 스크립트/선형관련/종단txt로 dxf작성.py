from tkinter import Tk, Label, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import os

def on_drop(event):
    # 드래그 앤 드롭된 파일 경로를 가져옵니다
    files = root.tk.splitlist(event.data)
    file_paths = [f for f in files if f.lower().endswith(('.txt'))]
    if not file_paths:
        label.config(text="txt 파일이 아닙니다.")
        return

    # 선택된 파일의 디렉토리 경로를 가져옵니다
    output_dir = os.path.dirname(file_paths[0])
    output_path = os.path.join(output_dir, "converted_dxf.dxf")

    # txt파일 파일열기
    points = txt_parsing(file_paths[0])

    #dxf content 작성
    dxf_content = create_polyline_dxf(points)
    # 결과를 파일에 저장
    try:
        with open(output_path, 'w') as f:
            f.write(dxf_content)
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

def create_polyline_dxf(points):
    dxf_content = f'''0
SECTION
2
HEADER
0
ENDSEC
0
SECTION
2
TABLES
0
ENDSEC
0
SECTION
2
BLOCKS
0
ENDSEC
0
SECTION
2
ENTITIES
0
POLYLINE
8
0
66
1
10
0
20
0
30
0
70
0
'''
    for point in points:
        x, y = point
        dxf_content += f'''0
VERTEX
8
0
10
{x}
20
{y}
30
0
70
32
'''
    dxf_content += '''0
SEQEND
0
ENDSEC
0
EOF
'''
    return dxf_content

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
