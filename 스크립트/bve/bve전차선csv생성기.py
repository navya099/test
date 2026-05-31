import os
from BVECSVObejct.csvobjectmodifyer import CSVObject


class CWWireBuilder:
    def __init__(self, length: int, systemheight: float):
        self.length = length
        self.systemheight = systemheight
        self.result = []

    def read_file(self, path, desc):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.readlines()
        else:
            raise FileNotFoundError(f"{desc} 파일을 찾을 수 없습니다.")

    def build(self, output_path: str):
        # 파일 읽기
        cw_file = rf'D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\무효용전차선_{self.length}m.csv'
        mw_file = rf'D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\무효용조가선_{self.length}m.csv'
        dropper_file = rf'D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\금구류\드로퍼클램프.csv'
        dropper_wire_file = rf'D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\공통\전선\드로퍼선.csv'

        cw_lines = self.read_file(cw_file, "cw")
        mw_lines = self.read_file(mw_file, "mw")
        dr_lines = self.read_file(dropper_file, "드로퍼")
        drw_lines = self.read_file(dropper_wire_file, "드로퍼 전선")

        # translate 적용
        csvmodifeye = CSVObject(mw_lines)
        mw_lines = csvmodifeye.translate(dx=0, dy=self.systemheight, dz=0)

        # 드로퍼 처리
        dropper_count = self.length // 5
        csvmodifeye.set_lines(dr_lines)
        ds, du = [], []
        for c in range(dropper_count):
            dz = c * 5
            ds.append(csvmodifeye.translate(dx=0, dy=0.015, dz=dz))
            du.append(csvmodifeye.translate(dx=0, dy=self.systemheight, dz=dz))

        # 드로퍼선 처리
        replaced_lines = []
        for line in drw_lines:
            if line.startswith("AddVertex"):
                replaced_lines.append(line.replace('13.0', str(self.systemheight)))
            else:
                replaced_lines.append(line)

        dwl = []
        csvmodifeye.set_lines(replaced_lines)
        for c in range(dropper_count):
            dz = c * 5
            dwl.append(csvmodifeye.translate(dx=0, dy=0, dz=dz))

        # 병합
        self.result.extend(cw_lines)
        self.result.extend(mw_lines)
        for d in ds: self.result.extend(d)
        for d in du: self.result.extend(d)
        for d in dwl: self.result.extend(d)

        # 저장
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(self.result)

        print(f"완성! 결과 파일은 {output_path} 에 저장되었습니다.")

if __name__ == '__main__':
    systemheight = 0.71
    for length in range(1, 64):  # 1 ~ 63까지
        if length in [35, 40, 45, 50, 55, 60]:  # 이미 존재하는 숫자는 제외
            continue

        try:
            builder = CWWireBuilder(length=length, systemheight=systemheight)
            output_file = rf"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력\일반철도\전선\전차선_가고{int(systemheight * 1000)}_{length}m.csv"
            builder.build(output_file)
        except FileNotFoundError as e:
            print(f"⚠️ {e} → {length}m 파일은 건너뜁니다.")
