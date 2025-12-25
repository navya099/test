# infrastructure/filesystem.py
import os

class FileSystemService:
    @staticmethod
    def ensure_directory(path, logger=None):
        if not os.path.exists(path):
            os.makedirs(path)
            if logger:
                logger(f"디렉토리 생성: {path}")
        else:
            if logger:
                logger(f"디렉토리 존재: {path}")

    @staticmethod
    def join_string_and_path(path, string):
        return os.path.join(path, string + '/')

    @staticmethod
    def copy_all_files(source_directory, target_directory, include_extensions=None, exclude_extensions=None):
        """
        원본 폴더의 모든 파일을 대상 폴더로 복사 (대상 폴더의 모든 데이터 제거)

        :param source_directory: 원본 폴더 경로
        :param target_directory: 대상 폴더 경로
        :param include_extensions: 복사할 확장자의 리스트 (예: ['.txt', '.csv'] → 이 확장자만 복사)
        :param exclude_extensions: 제외할 확장자의 리스트 (예: ['.log', '.tmp'] → 이 확장자는 복사 안 함)
        """

        # 대상 폴더가 존재하면 삭제 후 다시 생성
        if os.path.exists(target_directory):
            shutil.rmtree(target_directory)  # 대상 폴더 삭제
        os.makedirs(target_directory, exist_ok=True)  # 대상 폴더 재생성

        # 원본 폴더의 모든 파일을 가져와 복사
        for filename in os.listdir(source_directory):
            source_path = os.path.join(source_directory, filename)
            target_path = os.path.join(target_directory, filename)

            # 파일만 처리 (폴더는 복사하지 않음)
            if os.path.isfile(source_path):
                file_ext = os.path.splitext(filename)[1].lower()  # 확장자 추출 후 소문자로 변환

                # 포함할 확장자가 설정된 경우, 해당 확장자가 아니면 건너뛴다
                if include_extensions and file_ext not in include_extensions:
                    continue

                # 제외할 확장자가 설정된 경우, 해당 확장자는 복사하지 않는다
                if exclude_extensions and file_ext in exclude_extensions:
                    continue

                # 파일 복사 (메타데이터 유지)
                shutil.copy2(source_path, target_path)

        # 모든작업 종료후 원본폴더째로 삭제
        shutil.rmtree(source_directory)

        print(f"📂 모든 파일이 {source_directory} → {target_directory} 로 복사되었습니다.")

    @staticmethod
    def create_txt(output_file, data):
        with open(output_file, 'w', encoding='utf-8') as file:
            for line in data:
                file.write(line)