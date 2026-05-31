import os
import shutil
import pandas as pd

#전역변수
SHEET_ID = "1z0aUcuZCxOQp2St3icbQMbOkrSPfJK_8iZ2JKFDbW8c"
FREEOBJ_SHEET_NAME = "freeobj"  # ← 원하는 시트 이름
WALL_SHEET_NAME = "wall"
RAIL_SHEET_NAME = "rail"
DIKE_SHEET_NAME = "dike"
POLE_SHEET_NAME = "POLE"
FORM_SHEET_NAME = "FORM"
ROOF_SHEET_NAME = "ROOF"
GROUND_SHEET_NAME = "GROUND"
BACKGROUND_SHEET_NAME = "BACKGROUND"

# 원본 파일 5개 정의
src_files = [
    r"D:\BVE\루트\오브젝트.txt",
    r"D:\BVE\루트\프리오브젝트.txt",
    r"D:\BVE\루트\RAIL오브젝트.txt",
    r"D:\BVE\루트\WALL오브젝트.txt",
    r"D:\BVE\루트\DIKE오브젝트.txt",
    r"D:\BVE\루트\POLE오브젝트.txt",
]

dst_folder = r"D:\BVE\루트\Railway\Route"  # 하위폴더까지 탐색

class DFLibrary:
    def __init__(self, df):
        self.df = df

    def set_df(self, df):
        self.df = df

    def to_txt(self, column_name, filepath):
        """열의 모든 행을 txt 파일로 저장"""
        rows = self.df[column_name].tolist()
        with open(filepath, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(str(row) + "\n")

def create_url(sheetname):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheetname}"

def initialize_pd_csv(url):
    return pd.read_csv(url)

def sync_files(src_files, dst_folder):
    # 파일명 → 원본 경로 매핑
    src_map = {os.path.basename(p): p for p in src_files}

    for root, _, files in os.walk(dst_folder):
        # 세트 중 하나라도 발견되면 그 폴더를 대상 폴더로 간주
        intersect = set(src_map.keys()) & set(files)
        if intersect:
            for fname, src_path in src_map.items():
                dst_path = os.path.join(root, fname)
                if fname in files:
                    # 갱신 여부 확인
                    src_stat = os.stat(src_path)
                    dst_stat = os.stat(dst_path)
                    if (src_stat.st_mtime != dst_stat.st_mtime or
                        src_stat.st_size != dst_stat.st_size):
                        print(f"갱신: {dst_path}")
                        shutil.copy2(src_path, dst_path)
                else:
                    # 세트 내 다른 파일이 없으면 신규 복사
                    print(f"신규 복사: {dst_path}")
                    shutil.copy2(src_path, dst_path)


# 실행
if __name__ == "__main__":
    #1. 라이브러리 구축
    #URL로부터 DF 구축
    urllist = [
    create_url(RAIL_SHEET_NAME),
    create_url(DIKE_SHEET_NAME),
    create_url(WALL_SHEET_NAME),
    create_url(FORM_SHEET_NAME),
    create_url(ROOF_SHEET_NAME),
    create_url(FREEOBJ_SHEET_NAME),
    create_url(POLE_SHEET_NAME),
    create_url(GROUND_SHEET_NAME),
    create_url(BACKGROUND_SHEET_NAME)
    ]
    #2 각 url별 df 생성
    dflist = []
    for url in urllist:
        df = pd.read_csv(url)
        dflist.append(df)
    #3. 각 df별 txt생성
    liblist = []
    for df in dflist:
        lib = DFLibrary(df)
        liblist.append(lib)
    #4. txt로 저장
    filepaths = []
    for lib, name in zip(liblist,
                         [RAIL_SHEET_NAME, DIKE_SHEET_NAME, WALL_SHEET_NAME, FORM_SHEET_NAME,
                          ROOF_SHEET_NAME, FREEOBJ_SHEET_NAME, POLE_SHEET_NAME, GROUND_SHEET_NAME,
                          BACKGROUND_SHEET_NAME]):
        filepath = os.path.join("c:/temp/output", f"{name}.txt")
        lib.to_txt('취합', filepath)
        if name in [RAIL_SHEET_NAME,DIKE_SHEET_NAME, WALL_SHEET_NAME, FREEOBJ_SHEET_NAME , POLE_SHEET_NAME]:# 실제 열 이름 지정 필요
            filepaths.append(filepath)

    # 5 txt 병합 (roof, ground, form, background)
    merge_targets = [
        os.path.join("c:/temp/output", f"{ROOF_SHEET_NAME}.txt"),
        os.path.join("c:/temp/output", f"{GROUND_SHEET_NAME}.txt"),
        os.path.join("c:/temp/output", f"{FORM_SHEET_NAME}.txt"),
        os.path.join("c:/temp/output", f"{BACKGROUND_SHEET_NAME}.txt"),
    ]

    merged_file = os.path.join("c:/temp/output", "오브젝트.txt")

    with open(merged_file, "w", encoding="utf-8") as outfile:
        for fpath in merge_targets:
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
                    outfile.write("\n")  # 파일 사이에 줄바꿈 추가
            else:
                print(f"⚠️ 병합 대상 파일 없음: {fpath}")

    print(f"✅ 병합 완료: {merged_file}")

    #6 파일명 변경

    # 원하는 새 이름 매핑 (원하는 규칙에 맞게 수정)
    rename_map = {
        f"{DIKE_SHEET_NAME}.txt": f"{DIKE_SHEET_NAME.upper()}오브젝트.txt",
        f"{RAIL_SHEET_NAME}.txt": f"{RAIL_SHEET_NAME.upper()}오브젝트.txt",
        f"{FREEOBJ_SHEET_NAME}.txt": "프리오브젝트.txt",
        f"{WALL_SHEET_NAME}.txt": f"{WALL_SHEET_NAME.upper()}오브젝트.txt",
        f"{POLE_SHEET_NAME}.txt": f"{POLE_SHEET_NAME.upper()}오브젝트.txt",
    }

    new_filepaths = []
    for old_path in filepaths:
        if os.path.exists(old_path):
            folder = os.path.dirname(old_path)
            old_name = os.path.basename(old_path)
            new_name = rename_map.get(old_name)
            if new_name:
                new_path = os.path.join(folder, new_name)
                if os.path.exists(new_path):
                    os.remove(new_path)
                os.rename(old_path, new_path)
                print(f"✅ 파일명 변경: {old_name} → {new_name}")
                new_filepaths.append(new_path)  # 리스트에 새 이름 추가
            else:
                print(f"⚠️ 새 이름 매핑 없음: {old_name}")
                new_filepaths.append(old_path)  # 그대로 유지
        else:
            print(f"❌ 파일 없음: {old_path}")
            new_filepaths.append(old_path)

    filepaths = new_filepaths  # 갱신된 리스트로 교체

    # 7 D드라이브로 복사
    filepaths.append(merged_file)

    dst_root = r"D:\BVE\루트"

    for fpath in filepaths:
        if os.path.exists(fpath):
            try:
                shutil.copy2(fpath, dst_root)
                print(f"✅ 복사 완료: {fpath} → {dst_root}")
            except Exception as e:
                print(f"❌ 복사 실패: {fpath}, 오류: {e}")
        else:
            print(f"⚠️ 파일 없음: {fpath}")
    #8 동기화
    sync_files(src_files, dst_folder)