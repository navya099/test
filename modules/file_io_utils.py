import os
import shutil

def copy_all_files(source_directory, target_directory,
                   include_extensions=None, exclude_extensions=None,
                   delete_source=True, delete_target=False):
    """
    원본 폴더의 모든 파일을 대상 폴더로 복사 (옵션에 따라 원본/대상 삭제 가능)

    :param source_directory: 원본 폴더 경로
    :param target_directory: 대상 폴더 경로
    :param include_extensions: 복사할 확장자의 리스트 (예: ['.txt', '.csv'])
    :param exclude_extensions: 제외할 확장자의 리스트 (예: ['.log', '.tmp'])
    :param delete_source: True면 원본 폴더를 휴지통으로 이동
    :param delete_target: True면 대상 폴더를 휴지통으로 이동 후 재생성
    """

    # 대상 폴더 삭제 여부
    if os.path.exists(target_directory) and delete_target:
        shutil.rmtree(target_directory)
    os.makedirs(target_directory, exist_ok=True)

    # 확장자 리스트 소문자 변환
    if include_extensions:
        include_extensions = [ext.lower() for ext in include_extensions]
    if exclude_extensions:
        exclude_extensions = [ext.lower() for ext in exclude_extensions]

    # 파일 복사
    for filename in os.listdir(source_directory):
        source_path = os.path.join(source_directory, filename)
        target_path = os.path.join(target_directory, filename)

        if os.path.isfile(source_path):
            file_ext = os.path.splitext(filename)[1].lower()

            if include_extensions and file_ext not in include_extensions:
                continue
            if exclude_extensions and file_ext in exclude_extensions:
                continue

            shutil.copy2(source_path, target_path)

    # 원본 삭제 여부
    if delete_source:
        shutil.rmtree(source_directory)
        print(f"📂 {source_directory} → {target_directory} 복사 후 원본 폴더 휴지통 이동")
    else:
        print(f"📂 {source_directory} → {target_directory} 복사 완료 (원본 유지)")

def copy_files(file_list, target_path, overwrite=True):
    """
    여러 파일을 지정된 target_path로 복사하는 함수
    :param file_list: 복사할 파일 경로들의 리스트
    :param target_path: 대상 디렉토리 경로
    :param overwrite: True면 덮어쓰기, False면 기존 파일 유지
    """
    os.makedirs(target_path, exist_ok=True)

    for file_path in file_list:
        if os.path.isfile(file_path):
            dest_file = os.path.join(target_path, os.path.basename(file_path))
            if os.path.exists(dest_file) and not overwrite:
                print(f"⚠️ 이미 존재: {dest_file}, 덮어쓰기 안 함")
                continue
            try:
                shutil.copy(file_path, target_path)
                print(f"✅ 파일 복사 완료: {file_path} → {target_path}")
            except Exception as e:
                print(f"❌ 파일 복사 실패: {file_path}, 오류: {e}")
        else:
            print(f"⚠️ 파일 없음: {file_path}")