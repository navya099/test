import re
import os

def get_prefix(filename: str) -> str:
    return filename.replace("_index.txt", "").replace("_post.txt", "")

def rewrite_pair(index_file, post_file, start_index, log_entries):
    current = start_index
    new_index_lines = []

    # 선언부 번호 재배치
    with open(index_file, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            m = re.search(r"\.freeobj\((\d+)\)", line)
            if m:
                old = int(m.group(1))
                line = line.replace(f"({old})", f"({current})")
                log_entries.append(f"[선언부] {index_file}:{lineno} {old} → {current}")
                current += 1
            new_index_lines.append(line)

    with open(index_file, "w", encoding="utf-8") as f:
        f.writelines(new_index_lines)

    # 호출부 번호 재배치 (0은 새 번호, 1은 직전 번호 재사용)
    new_post_lines = []
    current = start_index
    last_number = None
    with open(post_file, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            parts = line.split(";")
            if len(parts) > 1 and parts[1].isdigit():
                old = int(parts[1])
                if "freeobj 1" in parts[0]:
                    # 상행 → 직전 하행 번호 재사용
                    if last_number is not None:
                        parts[1] = str(last_number)
                        log_entries.append(f"[호출부] {post_file}:{lineno} {old} → {last_number} (상행, 이전 번호 재사용)")
                else:
                    # 하행 → 새 번호 부여
                    parts[1] = str(current)
                    last_number = current
                    log_entries.append(f"[호출부] {post_file}:{lineno} {old} → {current} (하행, 새 번호)")
                    current += 1
            new_post_lines.append(";".join(parts))

    with open(post_file, "w", encoding="utf-8") as f:
        f.writelines(new_post_lines)

    return current

def collect_pairs(workdir):
    pairs = []
    for name in os.listdir(workdir):
        if name.endswith("_index.txt"):
            prefix = get_prefix(name)
            index_file = os.path.join(workdir, name)
            for root, dirs, files in os.walk(workdir):
                for fname in files:
                    if fname == prefix + "_post.txt":
                        post_file = os.path.join(root, fname)
                        pairs.append((index_file, post_file))
    return pairs

def main():
    start_index = int(input("새 인덱스 시작 번호를 입력하세요: "))
    workdir = r"D:\BVE\루트\Railway\Route\서울~진주"

    pairs = collect_pairs(workdir)
    log_entries = []

    for index_file, post_file in pairs:
        start_index = rewrite_pair(index_file, post_file, start_index, log_entries)

    # 로그 파일 저장
    log_path = os.path.join(workdir, "index_rewrite_log.txt")
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("=== FreeObj Index Rewrite Log ===\n")
        for entry in log_entries:
            log.write(entry + "\n")

    print("인덱스 재배치 완료! 로그 파일:", log_path)

if __name__ == "__main__":
    main()
