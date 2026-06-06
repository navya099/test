import pyperclip

# 사용자 입력 받기
print("원본 텍스트를 붙여넣고 Enter를 누르세요. (여러 줄 가능)")
print("입력 종료 후 Ctrl+D(mac/Linux) 또는 Ctrl+Z+Enter(Windows)로 마무리하세요.\n")

# 여러 줄 입력 받기
input_text = ""
try:
    while True:
        line = input()
        input_text += line + "\n"
except EOFError:
    pass

output_lines = []
for line in input_text.splitlines():
    parts = line.split(";")
    # Rail 또는 RailEnd가 포함된 모든 경우 (대소문자 무시)
    if len(parts) > 2 and ("rail" in parts[0].lower() or "railend" in parts[0].lower()):
        parts[2] = "0.0"   # Rail 뒤 두 번째 값 변경
        parts[3] = ""      # Rail 뒤 세 번째 값 제거
    output_lines.append(";".join(parts))

result = "\n".join(output_lines)

# 결과를 자동으로 클립보드에 복사
pyperclip.copy(result)

print("\n✅ 변환 완료! 결과가 클립보드에 복사되었습니다. Ctrl+V로 바로 붙여넣기 하세요.")