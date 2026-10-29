"""Reuse the original 本선선형계산v9.py engine with external JSON inputs."""
import argparse
import importlib.util
import json
import math
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="v9 평면선형 JSON 테스트 생성")
    parser.add_argument("--v9", required=True, help="본선선형계산v9.py 경로")
    parser.add_argument("--config", default="plan_test_config.json")
    parser.add_argument("--output", default="C:/temp/본선평면선형_IP검증.dxf")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    points = config["ip_points"]
    radii = config["radii"]
    if len(points) < 3 or len(radii) != len(points)-2:
        raise ValueError("ip_points 최소 3개, radii 개수는 IP 개수(점 개수-2)와 일치해야 합니다")
    if any(len(p) != 2 or not all(math.isfinite(float(v)) for v in p) for p in points):
        raise ValueError("ip_points는 유한한 [X,Y] 좌표 배열이어야 합니다")
    if any(not math.isfinite(float(r)) or float(r)<=0 for r in radii):
        raise ValueError("radii는 양의 유한값이어야 합니다")
    unit = int(config.get("unit",20))
    start_sta = float(config.get("start_sta",0))
    speed = float(config.get("maxV",70))
    scale = float(config.get("scale",1000))
    track_type = config.get("track_type","자갈도상")
    if not all(math.isfinite(x) for x in (unit,start_sta,speed,scale)) or min(unit,speed,scale)<=0:
        raise ValueError("unit, maxV, scale은 양의 유한값이어야 합니다")
    source=Path(args.v9).resolve()
    if not source.is_file():raise FileNotFoundError(source)
    spec=importlib.util.spec_from_file_location("rail_alignment_v9",source)
    v9=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v9)
    line=v9.LineString([(float(x),float(y)) for x,y in points])
    angles=v9.calculate_angles_and_plot(line)
    parameters=v9.cal_parameter([float(r) for r in radii],maxV=speed,track_type=track_type)
    result,report,fl=v9.calculate_curve(line,[float(r) for r in radii],angles,parameters,unit=int(unit),start_STA=start_sta)
    v9.unit=unit  # GUI-global dependency in original v9.create_dxf
    for i, row in enumerate(report, 1):
        kind = row[2]
        if kind == "cubic":
            stations = dict(zip(("SP", "PC", "CP", "PS"), row[19:23]))
        else:
            stations = dict(zip(("BC", "EC"), row[19:21]))
        print(f"[IP{i}] {kind} IA={row[6]:.4f} R={row[8]:.2f} 측점={stations}")
    output=Path(args.output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    v9.create_dxf(fl,line,report,result,filename=output.name,scale=scale)
    generated=Path("C:/temp")/output.name
    if generated.resolve()!=output:
        if not generated.exists():raise FileNotFoundError(f"v9 출력 경로를 확인하세요: {generated}")
        shutil.copy2(generated,output)
    print(f"[검증] IA={angles}, R={radii}, IP={len(radii)}, 출력={output}")
    import ezdxf
    doc=ezdxf.readfile(output)
    curve_labels = [e.dxf.text for e in doc.modelspace().query("TEXT[layer=='곡선제원문자']")]
    for tag in ("SP", "PC", "CP", "PS"):
        count = sum(t.startswith(tag + "=") for t in curve_labels)
        print(f"[DXF 검증] {tag}: {count}개")
    for ent in doc.modelspace().query("LWPOLYLINE[layer=='FL']"):
        coords=list(ent.get_points("xy"))
        length=sum(math.dist(a,b) for a,b in zip(coords,coords[1:]))
        print(f"[FL] 정점={len(coords)}, 직선근사길이={length:.3f}m, 유효측점={start_sta:.3f}~{start_sta+length:.3f}m")

if __name__ == "__main__":
    main()
