import ezdxf
import numpy as np


class DXFExporter:
    def __init__(self):
        """횡단면 데이터를 기반으로 표준 CAD DXF 도면을 생성하는 엑스포터"""
        pass
    @staticmethod
    def export_section(file_path, data):
        """
        단일 측점 데이터를 DXF 파일로 내보내기
        :param file_path: 저장할 DXF 파일 경로 (*.dxf)
        :param data: SectionProvider가 리턴한 단면 딕셔너리 데이터
        """
        # 1. 새 DXF 도면 생성
        doc = ezdxf.new('R2010')  # AutoCAD 2010 포맷
        msp = doc.modelspace()

        # 2. 표준 레이어 정의
        # 🚨 [버그 교정] dxfattribs의 키 명칭을 'linestyle'에서 'linetype'으로 수정했습니다.
        layers = [
            {"name": "01_EXIST_GROUND", "color": 3, "linetype": "CONTINUOUS"},  # 녹색 지반선
            {"name": "02_TRACK_BED", "color": 7, "linetype": "CONTINUOUS"},  # 흰색/검은색 노반
            {"name": "03_SLOPE_LEFT", "color": 5, "linetype": "CONTINUOUS"},  # 파란색 좌사면
            {"name": "04_SLOPE_RIGHT", "color": 1, "linetype": "CONTINUOUS"},  # 빨간색 우사면
            {"name": "05_TEXT", "color": 2, "linetype": "CONTINUOUS"},  # 노란색 문자 정보
        ]

        for layer in layers:
            doc.layers.new(
                name=layer["name"],
                dxfattribs={'color': layer["color"], 'linetype': layer["linetype"]}  # ◀ 교정 완료
            )

        # 3. 데이터 파싱 및 기하학적 기준점 정의
        center = data['center']
        fh_z = center[2]  # 계획고 (FH)
        gh_z = data['gl'] #지반고 GH()
        track_width = data.get('track_width', 8.0)
        half_w = track_width / 2.0

        # -------------------------------------------------------------
        # 📐 LINE 1: 선로 상면 노반선 (Track Bed)
        # -------------------------------------------------------------
        msp.add_line(
            start=(-half_w, fh_z),
            end=(half_w, fh_z),
            dxfattribs={'layer': '02_TRACK_BED', 'lineweight': 35}  # 0.35mm
        )

        # -------------------------------------------------------------
        # 📐 LINE 2: 좌측 설계 사면선 (Left Slope)
        # -------------------------------------------------------------
        ld = data['left_dist']
        _, elev_l = data['slope_l']

        msp.add_line(
            start=(-half_w - ld, elev_l),
            end=(-half_w, fh_z),
            dxfattribs={'layer': '03_SLOPE_LEFT', 'lineweight': 25}
        )

        # -------------------------------------------------------------
        # 📐 LINE 3: 우측 설계 사면선 (Right Slope)
        # -------------------------------------------------------------
        rd = data['right_dist']
        _, elev_r = data['slope_r']

        msp.add_line(
            start=(half_w, fh_z),
            end=(half_w + rd, elev_r),
            dxfattribs={'layer': '04_SLOPE_RIGHT', 'lineweight': 25}
        )

        # -------------------------------------------------------------
        # 📐 LINE 4: 원지반선 (Exist Ground) - 연속선(LWPolyline) 처리
        # -------------------------------------------------------------
        dist_g, elev_g = data['ground']

        # Matplotlib 차트와 완벽 싱크를 위해 횡축 부호 인버트 적용
        corrected_dist_g = -np.array(dist_g)
        ground_points = list(zip(corrected_dist_g, elev_g))

        msp.add_lwpolyline(
            points=ground_points,
            dxfattribs={'layer': '01_EXIST_GROUND', 'lineweight': 15}
        )

        # -------------------------------------------------------------
        # 🔤 TEXT: 측점 및 계획고 텍스트 마킹 (일반 TEXT 정렬 안정화)
        # -------------------------------------------------------------
        try:
            # format_distance 함수가 다른 파일에 정의되어 있다면 사용, 없으면 원본값 사용
            station_text = f"STATION: {data['station']}"
        except Exception:
            station_text = f"STATION: {data['station']}"

        fh_text = f"FH: {fh_z:.2f}m"
        gh_text = f"GH: {gh_z:.2f}m"
        # 🚨 [안정화 교정] add_text 엔티티의 정렬 방식을 일반 TEXT 문법에 맞춰 중앙 정렬(CENTER)로 제어합니다.
        t1 = msp.add_text(
            text=station_text,
            dxfattribs={'layer': '05_TEXT', 'height': 1.5, 'style': 'Standard'}
        )
        t1.set_placement((0, fh_z + 5.0), align=ezdxf.enums.TextEntityAlignment.CENTER)

        t2 = msp.add_text(
            text=fh_text,
            dxfattribs={'layer': '05_TEXT', 'height': 1.2, 'style': 'Standard'}
        )
        t2.set_placement((0, fh_z + 3.0), align=ezdxf.enums.TextEntityAlignment.CENTER)

        t3 = msp.add_text(
            text=gh_text,
            dxfattribs={'layer': '05_TEXT', 'height': 1.2, 'style': 'Standard'}
        )
        t3.set_placement((0, gh_z + 1.0), align=ezdxf.enums.TextEntityAlignment.CENTER)

        # 4. DXF 파일 저장
        doc.saveas(file_path)