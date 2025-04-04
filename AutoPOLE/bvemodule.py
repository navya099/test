from filemodule import *


class BVECSV:
    def __init__(self, poledata):
        self.poledata = poledata  # ✅ PoleDATAManager.poledata 인스턴스를 가져옴
        self.lines = []

    def create_pole_csv(self):
        self.lines.append(',;전주구문\n')
        data = self.poledata
        for i in range(len(data.poles) - 1):
            pos = data.poles[i].pos
            post_number = data.poles[i].post_number
            mastindex = data.poles[i].mast.index
            mastname = data.poles[i].mast.name
            bracketindex = data.poles[i].Brackets[0].index
            bracketname = data.poles[i].Brackets[0].name
            current_airjoint = data.poles[i].current_airjoint
            current_structure = data.poles[i].current_structure
            current_curve = data.poles[i].current_curve

            # 구문 작성
            self.lines.append(f',;{post_number}\n')
            self.lines.append(f',;-----{current_airjoint}({current_structure})({current_curve})-----\n')
            self.lines.append(f'{pos},.freeobj 0;{mastindex};,;{mastname}\n')
            self.lines.append(f'{pos},.freeobj 0;{bracketindex};,;{bracketname}\n\n')

    def create_csvtotxt(self):
        txthandler = TxTFileHandler()
        txthandler.save_file_dialog()  # 파일 저장 대화상자 열기
        txthandler.write_to_file(self.lines)
