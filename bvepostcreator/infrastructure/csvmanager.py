import os

class CSVManager:
    """CSV처리용 모듈"""
    @staticmethod
    def copy_and_export_csv(
        open_filename: str,
        output_filename: str,
        source_directory: str,
        work_directory: str,
        replacements: dict,
    ):
        """CSV의 문자열 편집
        Argumnets:
            open_filename: 원본 파일명
            output_filename: 사본 파일명
            source_directory: 소스폴더
            work_directory: 작업 폴더
            replacements: 교체할 문자열 딕셔너리
        """
        open_file = os.path.join(source_directory, f'{open_filename}.csv')
        output_file = os.path.join(work_directory, f'{output_filename}.csv')

        new_lines = []

        with open(open_file, 'r', encoding='utf-8') as f:
            for line in f:
                for old, new in replacements.items():
                    if old in line:
                        line = line.replace(old,new)
                new_lines.append(line)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    @staticmethod
    def insert_other_text(origin_filename: str, add_filename: str):
        """기존 파일의 최하단에 source_file의 모든 내용을 붙여넣기
        Argumnets:
            origin_filename: 원본 파일명
            source_directory: 소스폴더
            add_filename: 추가할 파일
            replacements: 교체할 문자열 딕셔너리

        """

        # 추가할 내용 읽기
        with open(add_filename, 'r', encoding='utf-8') as f:
            add_lines = f.readlines()
        try:
            with open(origin_filename, 'a', encoding='utf-8') as f:
                f.writelines(add_lines)
            print(f"✅ {origin_filename} 파일에 내용 추가 완료")
        except FileNotFoundError:
            print("❌ 파일을 찾을 수 없습니다.")