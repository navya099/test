import os
os.chdir("C:\\TEMP\\")
input_file = 'route.txt'
class RailBlockClassifier:
    def __init__(self, input_file):
        self.input_file = input_file
        self.blocks = self.classify_blocks()

    def classify_blocks(self):
        # 파일 내용을 읽어들입니다
        with open(self.input_file, "r") as f:
            lines = f.readlines()

        # 빈 줄을 기준으로 블록으로 나눕니다
        blocks = []
        block = []
        for line in lines:
            if line.strip().isdigit():
                if block:
                    blocks.append(block)
                    block = []
                block.append(line.strip())
            else:
                block.append(line.strip())
        if block:
            blocks.append(block)

        # 블록을 분류합니다
        result = {}
        for block in blocks:
            block_number = block[0]
            block_content = block[1:]

            if block_number not in result:
                result[block_number] = []

            for line in block_content:
                if '.rail 6;' in line:
                    if 'rail 6' not in result[block_number]:
                        result[block_number].append('rail 6')
                        result[block_number].append(line)
                elif '.rail 7;' in line:
                    if 'rail 7' not in result[block_number]:
                        result[block_number].append('rail 7')
                    result[block_number].append(line)

        return result

    def change(self):
        # 결과를 출력합니다
        for block_number, block_contents in self.blocks.items():
            for content in block_contents:
                if 'rail 6' in content:
                    print('rail number= 6\n,;rail 6')
                    for line in block_contents:
                        if '.rail 6;' in line:
                            print(f"{line.split(';')[0]},{line}")
                elif 'rail 7' in content:
                    print('rail number= 7\n,;rail 7')
                    for line in block_contents[:-1]:
                        if '.rail 7;' in line:
                            print(f"{line.split(';')[0]},{line}")
                    print(f"{block_contents[-1].split(';')[0]},{block_contents[-1]}")

classifier = RailBlockClassifier(input_file)
classifier.change()