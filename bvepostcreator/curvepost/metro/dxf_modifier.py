import ezdxf


class DXFModifier:
    @staticmethod
    def modify_curve_dxf(origin_file_path, new_file_path,
                         current_curve_type, current_radius,
                         current_cant, slack, tcl_value) -> bool:
        try:
            doc = ezdxf.readfile(origin_file_path)
            msp = doc.modelspace()
            layers = doc.layers
            # ... DXF 수정 로직 ...
            doc.saveas(new_file_path)
            return True
        except Exception as e:
            print(f"❌ DXF 텍스트 교체 실패: {e}")
            return False

    @staticmethod
    def modify_speed_limit_dxf(speedfile_path, modified_speedfile_path,
                               radius, speed_value) -> bool:
        try:
            doc = ezdxf.readfile(speedfile_path)
            msp = doc.modelspace()
            # ... 속도제한 DXF 수정 로직 ...
            doc.saveas(modified_speedfile_path)
            return True
        except Exception as e:
            print(f"❌ 속도 제한 DXF 텍스트 교체 실패: {e}")
            return False
