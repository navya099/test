from tkinter.filedialog import askopenfilename
import os
import pandas as pd
import chardet

import os
import shutil

import math

class CSVObject:
    """
    OPENBVE CSV오브젝트 조작용 클래스
    Attributes:
        lines: 대상 줄 리스트
    """
    def __init__(self, lines):
        self.lines = lines

    def get(self):
        return self.lines

    def translate(self, dx=0.0, dy=0.0, dz=0.0) -> list:
        """
        CSV오브젝트 Translate
        :param dx:
        :param dy:
        :param dz:
        :return: 새 줄
        """
        new_lines = []
        for line in self.lines:
            if line.strip().startswith('AddVertex'):
                parts = line.strip().split(',')
                try:
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    z = float(parts[3].strip())
                    # 좌표 이동
                    parts[1] = str(x + dx)
                    parts[2] = str(y + dy)
                    parts[3] = str(z + dz)
                    new_line = ','.join(parts) + '\n'
                    new_lines.append(new_line)
                except ValueError:
                    new_lines.append(line)  # 변환 실패하면 원본 그대로
            else:
                new_lines.append(line)
        self.lines = new_lines

    def scale(self, sx=1.0, sy=1.0, sz=1.0):
        """
        CSV오브젝트 Scale
        :param sx:
        :param sy:
        :param sz:
        :return:
        """
        new_lines = []
        for line in self.lines:
            if line.strip().startswith('AddVertex'):
                parts = line.strip().split(',')
                parts[1] = str(float(parts[1]) * sx)
                parts[2] = str(float(parts[2]) * sy)
                parts[3] = str(float(parts[3]) * sz)
                new_lines.append(','.join(parts))
            else:
                new_lines.append(line)
        self.lines = new_lines
        return self.lines

    def rotate(self, axis_x=0, axis_y=0, axis_z=0, angle=0.0):
        """
        CSV오브젝트 Rotate
        :param axis_x:
        :param axis_y:
        :param axis_z:
        :param angle:
        :return:
        """
        new_lines = []
        for line in self.lines:
            if line.strip().startswith('AddVertex'):
                new_lines.append(self._rotate_line(line, axis_x, axis_y, axis_z, angle))
            else:
                new_lines.append(line)
        self.lines = new_lines

    @staticmethod
    def _rotate_line(line, x, y, z, angle):
        if 'AddVertex' not in line:
            return line

        # 좌표 추출
        parts = line.strip().split(',')
        vx, vy, vz = float(parts[1]), float(parts[2]), float(parts[3])

        # 회전축 정규화
        length = math.sqrt(x ** 2 + y ** 2 + z ** 2)
        if length == 0:
            x, y, z = 1, 0, 0
        else:
            x, y, z = x / length, y / length, z / length

        theta = math.radians(angle)
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        one_minus_cos = 1 - cos_theta

        # Rodrigues' 회전
        new_x = (cos_theta + x * x * one_minus_cos) * vx + (x * y * one_minus_cos - z * sin_theta) * vy + (x * z * one_minus_cos + y * sin_theta) * vz
        new_y = (y * x * one_minus_cos + z * sin_theta) * vx + (cos_theta + y * y * one_minus_cos) * vy + (y * z * one_minus_cos - x * sin_theta) * vz
        new_z = (z * x * one_minus_cos - y * sin_theta) * vx + (z * y * one_minus_cos + x * sin_theta) * vy + (cos_theta + z * z * one_minus_cos) * vz

        parts[1] = str(new_x)
        parts[2] = str(new_y)
        parts[3] = str(new_z)
        return ','.join(parts)  + '\n'

    def mirror(self, mirror_x=0, mirror_y=0, mirror_z=0) -> list:
        """
        CSV오브젝트 Mirror
        :param mirror_x: X축 대칭 여부 (1이면 반전)
        :param mirror_y: Y축 대칭 여부 (1이면 반전)
        :param mirror_z: Z축 대칭 여부 (1이면 반전)
        :return: 변환된 줄 리스트
        """
        sx = -1 if mirror_x else 1
        sy = -1 if mirror_y else 1
        sz = -1 if mirror_z else 1

        # scale 함수 재활용
        return self.scale(sx, sy, sz)




class FileManager:
    """
    파일 관리용 클래스
    Attributes
        lib_manager: 라이브러리매니저
    """
    def __init__(self, lib_manager= None):
        self.lib_manager = lib_manager

    def copy_textures(self, texturefiles: list[str], dest_dir: str):
        """텍스처 파일을 지정 폴더로 복사
        Arguments:
            texturefiles: 텍스쳐 전체 경로리스트
            dest_dir: 타겟 경로
        """
        os.makedirs(dest_dir, exist_ok=True)
        for src in texturefiles:
            if os.path.exists(src):
                shutil.copy(src, dest_dir)

    def combine_file(self, selections: dict[str, str], gauge: float) -> tuple:
        """
        csv를 수집하여 조힙하는 메소드
        :param selections: gui에서 선택한 딕셔너리 객체(기둥,브래킷,급전선설비,보호선)
        :param gauge: 건식게이지
        :return: csv와 텍스쳐 경로 튜플
        """
        combine_lines = []
        texturefiles = []

        for category, filename in selections.items():
            if not filename:
                continue

            # 브래킷만 그룹별 탐색, 나머지는 공통(base)
            group = self.lib_manager.resolve_group(category, filename)

            # 실제 파일 경로 생성
            file_path = os.path.join(self.lib_manager.base_dir, group, category, filename)

            # 주석 추가
            combine_lines.append(f',;{file_path}\n')

            # 파일 내용 읽어서 추가
            lines = self.readfile(file_path)


            # 텍스처 검사
            for line in lines:
                texturename = self.search_texture_name(line)
                texturefile = self.lib_manager.get_texture_file(texturename)
                if texturefile:
                    texturefiles.append(texturefile)

            #건식게이지만큼 이동
            if category == '브래킷' or category == '금구류':
                csvparser = CSVObject(lines)
                lines = csvparser.translate(gauge)

            combine_lines.extend(lines)

        return combine_lines, texturefiles

    def readfile(self, filename: str) -> list[str]:
        """
        파일 읽기 메소드
        :param filename: 파일명
        :return: 문자열 리스트
        """
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return lines

    def search_texture_name(self, line: str) -> str:
        """LoadTexture 구문에서 텍스처 이름 추출
        :param line: 줄
        :return: 텍스쳐이름
        """
        line = line.strip()
        if line.startswith('LoadTexture'):
            parts = line.split(',')
            if len(parts) > 1:
                return parts[1].strip()
        return ''

    def save_csv(self, export_path: str, combine_lines: list[str]):
        """조립된 CSV 파일 저장
        :param export_path: 저장 경로
        :param combine_lines: csv
        """
        with open(export_path, 'w', encoding='utf-8') as f:
            for line in combine_lines:
                f.write(line)

def file_valid_check(filepath):
    # 헤더만 읽기

    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read(10000))  # 앞부분 샘플
    encoding = result['encoding']
    header_df = pd.read_csv(filepath, encoding=encoding, nrows=0)

    cols = header_df.columns.tolist()
    required = ['Station', 'Easting', 'Northing', 'Elevation', 'Bearing']

    return all(col in cols for col in required)

def read_civil3d_data(filepath):
    """엑셀 파일에서 좌표 리스트 얻기"""


    file_ext = os.path.splitext(filepath)[1].lower()
    #유효성 체크
    vaild = file_valid_check(filepath)
    if not vaild:
        raise Exception('지원하지 않는 파일입니다. 올바른 파일을 선택하세요')

    skiprows=0
    station_colum = 'Station'
    easting_colum = 'Easting'
    northing_colum = 'Northing'
    elevation_colum = 'Elevation'
    bearing_colum = 'Bearing'

    df = pd.read_csv(filepath, skiprows=skiprows)

    coords = df[[easting_colum, northing_colum]].values.tolist()
    elevations = df[elevation_colum].values.tolist()
    chainages = df[station_colum].values.tolist()
    bearings = df[bearing_colum].values.tolist()

    return chainages, coords, elevations, bearings

def main():
    while True:
        filepath = None
        file_select_cancled = False
        try:
            filepath = askopenfilename(title="절대좌표 CSV파일 선택")
            if not filepath:
                file_select_cancled = True
                raise FileNotFoundError("대상 파일을 찾을 수 없습니다")

            # Civil3D 데이터 읽기
            chainages, coords, elevations, bearings = read_civil3d_data(filepath)
            print(f"파일 읽기 성공: {filepath}")
            break

        except Exception as e:
            print(f"오류 발생: 파일: {filepath}, 에러: {e}")
            print("올바른 절대좌표 파일을 선택하세요.")
            if file_select_cancled:
                print("파일 선택을 취소하여 프로그램을 종료합니다.")
                exit(0)

    # CSV 오브젝트 불러오기
    csv_path = r'D:\BVE\루트\Railway\Object\철도표준라이브러리\궤도\표준단면\자갈도상\일반철도\5M레일_신선_전차선X.csv'
    save_obj_path = os.path.join("c:/temp", "openbveraillayout_test.csv")

    filemgr = FileManager()
    csv_lines = filemgr.readfile(csv_path)
    nlines = []

    for i, (sta, (x, y), z, azimuth) in enumerate(zip(chainages, coords, elevations, bearings)):
        csvobj = CSVObject(csv_lines)
        csvobj.translate(dx=x, dy=z, dz=y) #평면이동
        angle= 90 - math.degrees(azimuth) #북측 방위각으로 변환
        csvobj.rotate(axis_x=1, angle=angle) #XY평면회전(BVE에서는 XZ회전)

        # pitch 계산: 고도 변화량 / 거리 변화량
        if i < len(elevations) - 1:
            dz = elevations[i + 1] - elevations[i]
            dx = chainages[i + 1] - chainages[i]
            pitch = math.degrees(math.atan2(dz, dx))
        else:
            pitch = 0.0
        csvobj.rotate(axis_y=1, angle=pitch)  # YZ평면회전(BVE에서는 ZY회전)
        #다시 로컬 좌표로 변환
        center = [0,0,0] #기준점
        local_x = x - center[0] #로컬좌표X
        local_y = y - center[1] #로컬좌표Y
        local_z = z - center[2] #로컬좌표Z
        csvobj.translate(dx=local_x, dy=local_z, dz=local_y)
        nlines.extend(csvobj.get())
    filemgr.save_csv(save_obj_path, nlines)

if __name__ == '__main__':
    main()
