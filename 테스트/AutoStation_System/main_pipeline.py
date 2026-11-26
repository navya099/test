import os
import ezdxf
from ezdxf import units

from core.config_loader import load_or_create_config
from core.clash_projection_engine import build_existing_corridors
from dxf_builder.dxf_setup import setup_master_layers
from dxf_builder.view_plan import draw_master_plan_views
from dxf_builder.view_longitudinal import draw_master_longitudinal_view
from dxf_builder.view_cross_section import draw_master_cross_sections
from dxf_builder.view_integrated_shaft import draw_integrated_shaft_sections

def run_auto_station_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config", "master_config.json")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_dxf = os.path.join(output_dir, "AutoStation_Master_Verify.dxf")

    # 1. 마스터 설정 JSON 로드 (없으면 자동 생성)
    cfg = load_or_create_config(config_path)

    # 2. 기존 정거장(3개) + 기존 지하차도 + 지하보도 3D 폴리곤 및 이격경계 구축
    existing_objs = build_existing_corridors(cfg)

    # 3. DXF 도면 초기화 및 표준 레이어/선종 설정
    doc = ezdxf.new("R2018")
    doc.units = units.M
    setup_master_layers(doc)
    msp = doc.modelspace()

    # 4. 좌측 상단: 층별 평면도 + 기존 구조물 투영 + 수직구 평면 작도
    draw_master_plan_views(msp, cfg, existing_objs, base_offset=(20.0, 280.0))

    # 5. 좌측 하단: 곡선 전개 종단면도 + 지층선 + 3D 종단 투영 작도
    draw_master_longitudinal_view(msp, cfg, existing_objs, base_offset=(20.0, 20.0))

    # 6. 우측 상단: 대표 횡단면도(Box/아치터널) + 횡단 투영 작도
    draw_master_cross_sections(msp, cfg, existing_objs, base_offset=(240.0, 260.0))

    # 7. 우측 하단: 출입구 겸용 통합수직구 종·횡단 3면도 작도
    draw_integrated_shaft_sections(msp, cfg, base_offset=(240.0, 110.0))

    # 8. 최종 DXF 저장
    doc.saveas(output_dxf)
    print(f"[SUCCESS] 전체 통합 자동설계 검증 도면 생성 완료: {output_dxf}")

if __name__ == "__main__":
    run_auto_station_pipeline()
