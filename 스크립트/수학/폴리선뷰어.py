import pandas as pd
import matplotlib.pyplot as plt
from tkinter import filedialog, ttk

# CSV 파일 경로를 지정합니다.
filepath = filedialog.askopenfilename() # Open file dialog
csv_file_path = filepath

# CSV 파일을 읽어 데이터프레임으로 변환합니다.
# CSV 파일을 헤더 없이 읽고 열 이름을 수동으로 지정합니다.
df = pd.read_csv(csv_file_path, header=None, names=['sta', 'xcoord', 'ycoord'])

# 데이터프레임의 내용을 출력하여 확인합니다.
print(df)

# 그래프를 생성합니다.
plt.figure(figsize=(10, 6))

# x좌표와 y좌표를 플로팅합니다.
plt.plot(df['xcoord'], df['ycoord'], c='red', label='Coordinates')

# 제목과 라벨을 추가합니다.
plt.axis('equal')
plt.title('Scatter Plot of Coordinates')
plt.xlabel('X Coordinate')
plt.ylabel('Y Coordinate')
plt.legend()

# 그래프를 출력합니다.
plt.show()
