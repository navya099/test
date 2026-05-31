def read_coordinates(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        
    data = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) == 2:
            sta = parts[0].strip()
            radius = parts[1].strip()
            #cant = parts[2].strip()
            data.append(f"{sta},{radius}")  # y 값을 1000으로 곱하고 소수점 다섯 자리로 포맷팅
    
    return data

def parsing_data(data, out_file):
    # 결과를 저장할 리스트
    result = []

    # 값을 추적하기 위한 세트
    seen_values = set()

    # 데이터 순회
    for line in data:
        key, value = line.split(',')
        if value not in seen_values:
            result.append(line)
            seen_values.add(value)
        else:
            # 이전 값이 현재 값과 같은 경우 추가
            if len(result) > 0 and result[-1].split(',')[1] != value:
                result.append(line)

    with open(out_file, 'w') as file:
        file.writelines('\n'.join(result) + '\n')
        
def main():
    input_file = 'c:/temp/curve_info.txt'
    out_file = 'c:/temp/curve_info_out.txt'
    data = read_coordinates(input_file)
    parsing_data(data, out_file)
    
    print(f"Output file created successfully at {out_file}")

if __name__ == "__main__":
    main()
