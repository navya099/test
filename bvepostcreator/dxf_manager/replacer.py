import ezdxf


class DXFReplacer:
    """dxf 텍스트 리플레이서"""
    @staticmethod
    def replace_text_in_dxf(file_path, modified_path, sta, grade, seg, R):
        """DXF 파일의 특정 텍스트를 새 텍스트로 교체하고, 특정 레이어 가시성을 조절하는 메서드"""
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()

            # 🟢 특정 레이어의 TEXT 엔티티 찾아서 교체
            for entity in msp.query("TEXT"):
                if entity.dxf.layer == "측점":
                    if len(sta) == 5:  # 3.456
                        sta = ' ' + sta

                    entity.dxf.text = sta  # STA 변경
                    if len(sta) == 7:  # 123.456
                        entity.dxf.width = 0.9

                elif entity.dxf.layer == "구배":
                    if len(grade) == 1:  # 2
                        grade = grade + ' '
                    entity.dxf.text = grade  # 구배 변경
                elif entity.dxf.layer == "R":
                    if R != 'None':
                        entity.dxf.text = R  # 종곡선반경 변경
            # 🟢 레이어 가시성 조절 (볼록형: 표시, 오목형: 숨김)
            layers = doc.layers

            if seg == '오목형':
                layers.get(seg).on()
                layers.get('볼록형').off()

            elif seg == '볼록형':
                layers.get(seg).on()
                layers.get('오목형').off()

            # 변경된 DXF 저장
            doc.saveas(modified_path)
            # print("✅ DXF 수정 완료")
            return True

        except Exception as e:
            print(f"❌ DXF 수정 실패: {e}")
            return False