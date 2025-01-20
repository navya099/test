import csv
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import os

# 기본 작업 디렉토리
default_directory = 'c:/temp/object/'
work_directory = None
# 사용자가 설정한 작업 디렉토리가 없으면 기본값 사용
if not work_directory:
    work_directory = default_directory

# 디렉토리가 존재하지 않으면 생성
if not os.path.exists(work_directory):
    os.makedirs(work_directory)

print(f"작업 디렉토리: {work_directory}")
    
def format_distance(number, decimal_places=2):
    negative = False
    if number < 0:
        negative = True
        number = abs(number)
        
    km = int(number) // 1000
    remainder = round(number % 1000, decimal_places)  # Round remainder to the specified decimal places
    
    # Format the remainder to have at least 'decimal_places' digits after the decimal point
    formatted_distance = "{:d}km{:0{}.{}f}".format(km, remainder, 4 + decimal_places, decimal_places)
    
    if negative:
        formatted_distance = "-" + formatted_distance
    
    return formatted_distance

def read_file():
    file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("txt files", "*.txt"), ("All files", "*.*")])
    print('현재파일:', file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            lines = list(reader)
    except UnicodeDecodeError:
        print('현재파일은 utf-8인코딩이 아닙니다. euc-kr로 시도합니다.')
        try:
            with open(file_path, 'r', encoding='euc-kr') as file:
                reader = csv.reader(file)
                lines = list(reader)
        except UnicodeDecodeError:
            print('현재파일은 euc-kr인코딩이 아닙니다. 파일을 읽을 수 없습니다.')
            return []
    return lines

def process_sections(data):
    sections = []
    current_section = []

    for row in data:
        try:
            station, radius = map(float, row)
            station = int(station)
        except ValueError:
            print(f"잘못된 데이터 형식: {row}")
            continue

        current_section.append((station, radius))

        if radius == 0.0 and current_section:
            sections.append(current_section)
            current_section = []

    return sections

def annotate_sections(sections):
    annotated_sections = []

    for section in sections:
        if not section:
            continue

        annotated_section = []
        n = len(section)

        for i, (station, radius) in enumerate(section):
            annotation = ""

            # 첫 번째 줄에 SP 추가
            if i == 0:
                annotation += ";SP"
            
            # 마지막 줄에 PS 추가
            if i == n - 1:
                annotation += ";PS"

            # STA 간 차이가 25보다 큰 경우 PC/CP 추가
            if i < n - 1:  # Ensure we're not at the last row
                prev_station, prev_radius = section[i - 1] if i > 0 else (None, None)
                next_station, next_radius = section[i + 1]
                
                if next_station - station > 75:
                    annotation += ";PC"
                elif i > 0 and station - prev_station > 75:
                    annotation += ";CP"

            annotated_section.append(f"{station},{radius}{annotation}")

        # SP와 PS만 있는 구간을 BC와 EC로 변경
        if len(annotated_section) == 2 and ";SP" in annotated_section[0] and ";PS" in annotated_section[1]:
            annotated_section[0] = annotated_section[0].replace(";SP", ";BC")
            annotated_section[1] = annotated_section[1].replace(";PS", ";EC")

        annotated_sections.append(annotated_section)

    return annotated_sections


def create_text_image(text, bg_color, filename, image_size=(500, 300), font_size=40):
    # 이미지 생성 (배경색: 검정색)
    img = Image.new('RGB', image_size, color=bg_color)
    
    # 드로잉 객체 생성
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정 (굴림체 폰트 사용)
    font = ImageFont.truetype("gulim.ttc", font_size)
    
    # 텍스트 경계 상자 계산
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # 중앙에 배치할 텍스트의 좌상단 시작 위치 계산
    text_position = (
        (image_size[0] - text_width) // 2,  # 가로 중앙
        (image_size[1] - text_height) // 2  # 세로 중앙
    )
    
    # 글자 색상 설정 (빨간색)
    text_color = (255, 255, 255)

    # 이미지에 글자 추가
    draw.text(text_position, text, font=font, fill=text_color)

    # 이미지 저장
    # 파일 확장자 추가
    if not filename.endswith('.png'):
        filename += '.png'
    final_dir = work_directory + filename
    img.save(final_dir)

def create_csv(filename):
    output_file = work_directory + filename + '.csv'
    with open(output_file, 'w', encoding='utf-8') as file:
        content = ";Create By dger\n"
        content += '\nCreateMeshBuilder\n'
        content += 'AddVertex, 0,0,0\n'   
        content += 'AddVertex, 0.5,0,0\n'
        content += 'AddVertex, 0.5,-0.4,0\n'
        content += 'AddVertex, 0,-0.4,0\n'
        content += 'AddFace , 0,1,2,3\n'
        content += f'LoadTexture, {filename}.png\n'
        content += 'SetTextureCoordinates, 0, 0, 0\n'
        content += 'SetTextureCoordinates, 1, 1, 0\n'
        content += 'SetTextureCoordinates, 2, 1, 1\n'
        content += 'SetTextureCoordinates, 3, 0, 1\n'
        content += '\nCreateMeshBuilder\n'
        content += 'Cylinder, 6, 0.05, 0.05, 2\n'
        content += 'Translate, 0.2, -1, 0.1\n'
        content += 'TranslateAll, -0.2, 2, 0\n'
        content += ';EOF'
        
        file.write(content)
        
def create_object_index(data):
    output_file = work_directory + 'object_index.txt'
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(data)

def parse_sections(file_content):
    """
    파일 내용에서 각 구간과 태그를 파싱하여 리스트로 반환.
    """
    sections = {}
    current_section = None

    for line in file_content:  # file_content는 csv.reader가 반환한 리스트 형태
        # 리스트 형태의 line을 문자열로 변환
        line = ",".join(line)
        
        if line.startswith("구간"):
            current_section = int(line.split()[1][:-1])
            sections[current_section] = []
        elif current_section is not None and line.strip():
            sta, rest = line.split(',', 1)
            sta = int(sta)
            radius_tag = rest.split(';')
            radius = float(radius_tag[0])
            tags = radius_tag[1:] if len(radius_tag) > 1 else []
            sections[current_section].append((sta, radius, tags))

    return sections


def parse_object_index(index_content):
    """
    object_index.txt 내용을 파싱하여 태그별 인덱스 매핑을 반환.
    """
    tag_mapping = {}

    for row in index_content:  # row는 리스트 형태
        if len(row) != 1:  # 한 줄이 하나의 문자열로 되어 있어야 함
            print(f"잘못된 줄 형식 건너뜀: {row}")
            continue

        line = row[0]  # 리스트 내부의 문자열을 꺼냄
        parts = line.split()  # 공백으로 분리
        if len(parts) < 2:  # 최소한 2개의 요소가 있어야 함
            print(f"잘못된 줄 형식 건너뜀: {line}")
            continue

        try:
            obj_name = parts[1].split('/')[-1].split('.')[0]  # e.g., 구간1_SP
            obj_index = int(parts[0].split('(')[-1].rstrip(')'))
            tag_mapping[obj_name] = obj_index
        except (IndexError, ValueError) as e:
            print(f"오류 발생: {e} - 줄 내용: {line}")
            continue

    return tag_mapping



def find_object_index(sta, sections, tag_mapping):
    """
    STA 값에 해당하는 구간과 태그를 찾아 오브젝트 인덱스를 반환.
    """
    for section_id, points in sections.items():
        for i, (start_sta, _, tags) in enumerate(points):
            if sta == start_sta:  # STA가 정확히 일치하는 경우
                for tag in tags:
                    key = f"구간{section_id}_{tag}"
                    if key in tag_mapping:
                        return tag_mapping[key]
    return None
def create_curve_post_txt(data_list):
    """
    결과 데이터를 받아 파일로 저장하는 함수.
    """
    output_file = work_directory + "curve_post.txt"  # 저장할 파일 이름
    with open(output_file, "w", encoding="utf-8") as file:
        if isinstance(data_list, list):  # data_list가 리스트인 경우
            # 리스트 요소들을 문자열로 변환하고 파일에 작성
            file.write("".join(map(str, data_list)))
        else:
            # data_list가 문자열이라면 바로 작성
            file.write(str(data_list))

        
# 파일 읽기
data = read_file()

if not data:
    print("데이터가 비어 있습니다.")
else:
    # 구간 정의 및 처리
    sections = process_sections(data)
    annotated_sections = annotate_sections(sections)

    # 결과 파일 저장
    output_file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("txt files", "*.txt"), ("All files", "*.*")])
    if not output_file:
        print("출력 파일을 선택하지 않았습니다.")
    else:
        with open(output_file, 'w', encoding='utf-8') as file:
            for i, section in enumerate(annotated_sections, start=1):
                file.write(f"구간 {i}:\n")
                for line in section:
                    file.write(f"{line}\n")
                file.write("\n")

        print(f"주석이 추가된 결과가 {output_file}에 저장되었습니다.")

    #이미지 저장
    PC_R_LIST = []
    last_PC_radius = None  # 마지막 PC 반지름을 추적
    objec_index_name = ''
    image_names = []
    objec_index_counter = 2025  # 시작 번호 설정
    
    for i, section in enumerate(annotated_sections, start=1):
        # 1구간에 SP와 PS만 있는 경우를 확인
        if len(section) == 2 and 'SP' in section[0] and 'PS' in section[1]:
            section[0] = section[0].replace(";SP", ";BC")  # SP를 BC로 변경
            section[1] = section[1].replace(";PS", ";EC")  # PS를 EC로 변경
        for line in section:
            if 'BC' in line or 'EC' in line or 'SP' in line or 'PC' in line or 'CP' in line or 'PS' in line:
                
                parts = line.split(',')
                sta = int(parts[0])
                parts2 =  parts[1].split(';')
                radius = float(parts2[0])
                
                if radius < 0:
                    radius *= -1
                sec = parts2[1] if len(parts2) > 1 else None
                
                if 'SP' in line:
                    img_text = f'SP= {format_distance(sta, decimal_places=2)}'
                    img_bg_color = (34, 139, 34)
                    img_f_name = f'구간{i}_SP'
                    
                elif 'PC' in line:
                    img_text = f'PC= {format_distance(sta, decimal_places=2)}\nR={radius}\nC=60'
                    img_bg_color = (255, 0, 0)
                    img_f_name = f'구간{i}_PC'
                    PC_R_LIST.append(radius)
                    last_PC_radius = radius
                    
                elif 'CP' in line:
                    if last_PC_radius is not None:
                        img_text = f'CP= {format_distance(sta, decimal_places=2)}\nR={last_PC_radius}\nC=60'
                    else:
                        img_text = f'CP= {format_distance(sta, decimal_places=2)}\nR=Unknown\nC=60'
                    img_bg_color = (255, 0, 0)
                    img_f_name = f'구간{i}_CP'
                    
                elif 'PS' in line:
                    img_text = f'PS= {format_distance(sta, decimal_places=2)}'
                    img_bg_color = (34, 139, 34)
                    img_f_name = f'구간{i}_PS'

                elif 'BC' in line:
                    img_text = f'BC= {format_distance(sta, decimal_places=2)}'
                    img_bg_color = (255, 0, 0)
                    img_f_name = f'구간{i}_BC'

                elif 'EC' in line:
                    img_text = f'EC= {format_distance(sta, decimal_places=2)}'
                    img_bg_color = (255, 0, 0)
                    img_f_name = f'구간{i}_EC'
                    
                else:
                    print('에러')
                    img_text = 'DPFJ'
                    img_bg_color = (0, 0, 0)
                    img_f_name = '에러'
                    
                create_text_image(img_text, img_bg_color, img_f_name, image_size=(500, 300), font_size=40)
                create_csv(img_f_name)
                image_names.append(img_f_name)
                
        #2025부터 끝까지                 
        # 객체 인덱스 생성
        objec_index_name = ""
        for img_name in image_names:
            objec_index_name += f".freeobj({objec_index_counter}) abcdefg/{img_name}.CSV\n"
            objec_index_counter += 1  # 카운터 증가

        
        
    create_object_index(objec_index_name)

# 데이터 파싱
opendata = work_directory + '1532326.txt'
with open(opendata, 'r', encoding='utf-8') as file:
            reader1 = csv.reader(file)
            lines1 = list(reader1)
            
OBJ_DATA = work_directory + 'object_index.txt'

with open(OBJ_DATA, 'r', encoding='utf-8') as file:
            reader2 = csv.reader(file)
            lines2 = list(reader2)
            
sections = parse_sections(lines1)

tag_mapping = parse_object_index(lines2)

# STA 값 검색
result_list =[]

for section_id, entries in sections.items():  # 모든 구간을 순회
    for sta_value, radius, tags in entries:  # 각 구간의 엔트리를 순회

        result = find_object_index(sta_value, sections, tag_mapping)

        '''
        # 결과 출력
        if result:
            print(f"STA {sta_value}에 대한 오브젝트 인덱스: {result}")
        else:
            print(f"STA {sta_value}에 대한 오브젝트 인덱스를 찾을 수 없습니다.")
        '''

        if not result == None:
            result_data = f'{sta_value},.freeobj 0;{result};\n'
            result_list.append(result_data)
        
#csv작성
create_curve_post_txt(result_list)


