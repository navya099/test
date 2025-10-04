import os
import shutil
from csvobject import CSVObject


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