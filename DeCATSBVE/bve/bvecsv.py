from utils.comom_util import offsets


class BVECSV:
    """BVE CSV 구문을 생성하는 클래스
    Attributes:
        poledata (PoleDATAManager): PoleDATAManager.poledata 인스턴스
        wiredata (WireDataManager): WireDataManager.wiredata 인스턴스
        lines (list[str]]): 구문 정보를 저장할 문자열 리스트
    """

    def __init__(self, poledata=None, wiredata=None, track_index=None):
        self.poledata = poledata  # ✅ PoleDATAManager.poledata 인스턴스를 가져옴
        self.wiredata = wiredata
        self.track_index = track_index
        self.lines = []

    def create_pole_csv(self):
        """전주 구문 생성 메서드"""
        self.lines = []

        def write_equipment(pos, eqs):
            for eq in eqs:
                self.lines.append(
                    f'{pos},.freeobj {self.track_index};{eq.index};{eq.offset[0]};{eq.offset[1]};{eq.rotation};,;{eq.name}\n'
                )

        def write_mast(pos, mast):
            self.lines.append(
                f'{pos},.freeobj {self.track_index};{mast.index};{mast.offset};0;{mast.rotation};,;{mast.name}\n'
            )

        def write_brackets(pos, brs):
            for br in brs:
                self.lines.append(
                    f'{pos},.freeobj {self.track_index};{br.index};{br.offset[0]};{br.offset[1]};{br.rotation},;{br.bracket_name}\n'
                )
                write_fittings(pos, br.fittings)

        def write_fittings(pos, fittings):
            for fit in fittings:
                self.lines.append(
                    f'{pos},.freeobj {self.track_index};{fit.index};{fit.offset[0]};{fit.offset[1]};{fit.rotation};,;{fit.label}\n'
                )

        for pole in self.poledata:
            try:
                pos = pole.pos
                post_number = pole.post_number
                section = pole.section
                structure = pole.structure
                curve = '직선' if pole.radius == 0.0 else '곡선'
                eqs = pole.equipments
                brs = pole.brackets
                mast = pole.mast
                section_label = section if section else '일반개소'

                self.lines.append(f',;{post_number}\n')
                self.lines.append(f',;-----{section_label}({structure})({curve})-----\n')

                if section is None:
                    write_equipment(pos, eqs)
                    write_mast(pos, mast)
                    write_brackets(pos, brs)

                elif section in ['에어조인트 시작점 (1호주)', '에어조인트 끝점 (5호주)']:
                    write_mast(pos, mast)
                    write_brackets(pos, [brs[0]])
                    write_equipment(pos, eqs)

                elif section in ['에어조인트 (2호주)', '에어조인트 중간주 (3호주)', '에어조인트 (4호주)']:
                    poss = (pos - 0.528, pos + 0.528) if section in ['에어조인트 (2호주)', '에어조인트 (4호주)'] else (
                    pos - 0.8, pos + 0.8)
                    write_mast(pos, mast)
                    write_equipment(pos, eqs)
                    for p, br in zip(poss, brs):
                        self.lines.append(',;가동브래킷구문\n')
                        write_brackets(p, [br])

            except AttributeError as e:
                print(f"poledata 데이터 누락: {pos}, 오류: {e}")
            except Exception as e:
                print(f"예상치 못한 오류: {pos}, 오류: {e}")

        print('create_pole_csv 실행이 완료됐습니다.')
        return self.lines

    def create_wire_csv(self):
        """
        전선 구문 생성 메서드
        """
        self.lines = []  # 코드 실행전 초기화
        for pole, wire in zip(self.poledata, self.wiredata):
            try:
                pos = pole.pos
                post_number = pole.post_number
                section = pole.section
                structure = pole.structure
                curve = '직선' if pole.radius == 0.0 else '곡선'
                section_label = section if section else '일반개소'

                # 구문 작성
                self.lines.append(f',;{post_number}\n')
                self.lines.append(f',;-----{section_label}({structure})({curve})-----\n')

                for wr in wire.wires:
                    sta = wr.station if wr.station else pos
                    self.lines.append(f'{sta},.freeobj {self.track_index};{wr.index};{wr.offset[0]};{wr.offset[1]};{wr.adjusted_angle};{wr.topdown_angle};0;,;{wr.label}\n')

            except AttributeError as e:
                print(f"Wire 데이터 누락: index {pos}, 오류: {e}")
            except Exception as e:
                print(f"예상치 못한 오류: index {pos}, 오류: {e}")

        print(f'create_wire_csv실행이 완료됐습니다.')
        return self.lines