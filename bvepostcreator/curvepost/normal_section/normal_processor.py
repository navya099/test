import ezdxf


class NormalSectionProcessor:
    """일밴개소용 곡선표처리"""
    @staticmethod
    def processs(file_path, modifed_path, new_text):
        """DXF 파일의 특정 텍스트를 새 텍스트로 교체하는 함수"""
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()

            # 교체할 텍스트 결정 (텍스트 길이에 따라)
            text_mapping = {
                3: '100',
                4: '2000',
                5: '15000',
                6: '150000'
            }
            old_text = text_mapping.get(len(new_text), None)

            if old_text is None:
                print(f"⚠️ 지원되지 않는 텍스트 길이: {new_text}")
                return False

            # DXF 텍스트 엔티티 수정
            for entity in msp.query("TEXT"):
                if entity.dxf.text == old_text:
                    entity.dxf.text = new_text  # 텍스트 교체
                else:
                    entity.dxf.text = ''  # 나머지 텍스트 삭제

            # 변경된 DXF 저장
            doc.saveas(modifed_path)

            return True

        except Exception as e:
            print(f"❌ DXF 텍스트 교체 실패: {e}")
            return False