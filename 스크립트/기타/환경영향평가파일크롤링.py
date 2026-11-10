from pathlib import Path
import subprocess
import os

START_SEQ = 3303299
END_SEQ = 3303483

SAVE_DIR = Path("downloads")
SAVE_DIR.mkdir(exist_ok=True)

os.chdir(SAVE_DIR)
def get():
    for seq in range(START_SEQ, END_SEQ + 1):
        url = (
            "https://eiass.go.kr/common/file/"
            f"downloadFileByFileSeq.do?FILE_SEQ={seq}"
        )

        print(f"다운로드 시도: {seq}")

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-L",   # 리다이렉트 허용
                    "-O",   # 파일 저장
                    "-J",   # 서버 파일명 사용
                    "--silent",
                    "--show-error",
                    url
                ],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"완료: {seq}")
            else:
                print(f"실패: {seq}")
                print(result.stderr)

        except Exception as e:
            print(f"예외: {seq} - {e}")


from pathlib import Path
from urllib.parse import unquote


def decode_utf8_filename(folder):
    for file in folder.iterdir():
        if not file.is_file():
            continue

        new_name = unquote(file.name)
        new_name = new_name.replace("+", " ")

        new_path = file.with_name(new_name)

        if new_path != file:
            file.rename(new_path)
            print(f"{file.name} -> {new_name}")

if __name__ == "__main__":
    get()
    decode_utf8_filename(Path("."))