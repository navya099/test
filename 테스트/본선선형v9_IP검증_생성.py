"""본선선형계산v9.py의 계산 및 DXF 출력 함수를 재사용하는 IP 검증 도면 생성기."""
from pathlib import Path
import importlib.util
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--v9', default='본선선형계산v9.py', help='원본 v9 파이썬 파일')
    parser.add_argument('--output', default='C:/temp/본선평면선형_IP검증.dxf')
    parser.add_argument('--start-sta', type=float, default=0)
    args = parser.parse_args()
    source = Path(args.v9).resolve()
    if not source.is_file():
        raise FileNotFoundError(f'원본 v9 파일을 찾지 못했습니다: {source}')
    spec = importlib.util.spec_from_file_location('rail_alignment_v9', source)
    v9 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v9)

    # 토목좌표 (X,Y), 반경은 중간 IP에만 지정. 직선 500m + 작은 교각 10도.
    points = [(0., 0.), (500., 0.), (992.4038765, 86.8240888)]
    radius = [600.]
    line = v9.LineString(points)
    angles = v9.calculate_angles_and_plot(line)
    parameters = v9.cal_parameter(radius, maxV=70, track_type='자갈도상')
    result, report, fl = v9.calculate_curve(line, radius, angles, parameters, unit=20, start_STA=args.start_sta)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    # v9 내부 저장 함수는 C:/temp/ 접두어를 강제하므로, 파일명만 전달하고 생성물을 이동한다.
    # v9 GUI에서 설정하는 전역 측점 간격을 비GUI 실행 시 명시적으로 초기화
    v9.unit = 20
    v9.create_dxf(fl, line, report, result, filename=output.name, scale=1000)
    generated = Path('C:/temp') / output.name
    if generated.resolve() != output and generated.exists():
        import shutil
        shutil.copy2(generated, output)
    print(f'[검증] IA={angles}, R={radius}, IP=1, 출력={output}')

if __name__ == '__main__':
    main()
