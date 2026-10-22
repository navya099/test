# scene.py
import math

# 표준 도면 레이어 정의
LAYERS = [
    {'name': 'C-TOPO-MINR', 'token': 'minor', 'aci': 8, 'label': '주곡선'},
    {'name': 'C-TOPO-MAJR', 'token': 'major', 'aci': 7, 'label': '계곡선'},
    {'name': 'C-TOPO-TEXT', 'token': 'major', 'aci': 7, 'label': '등고선 주기'},
    {'name': 'C-TOPO-TINN', 'token': 'tin', 'aci': 8, 'label': '삼각망'},
    {'name': 'C-TOPO-BRKL', 'token': 'orange', 'aci': 30, 'label': '경계선'},
    {'name': 'C-TOPO-BNDY', 'token': 'ink2', 'aci': 7, 'label': '외곽 경계'},
    {'name': 'C-TOPO-SLOP', 'token': 'cyan', 'aci': 4, 'label': '경사 방향'},
    {'name': 'V-NODE', 'token': 'green', 'aci': 3, 'label': '측량점'},
    {'name': 'V-NODE-TEXT', 'token': 'green', 'aci': 3, 'label': '측량점 주기'},
    {'name': 'V-NODE-LINE', 'token': 'green', 'aci': 3, 'label': '측량 심볼선'},
    {'name': 'C-ROAD-CNTR', 'token': 'red', 'aci': 1, 'label': '선형 중심선'},
    {'name': 'C-ROAD-STAN', 'token': 'red', 'aci': 1, 'label': '측점 및 표시'},
    {'name': 'C-ROAD-CORR', 'token': 'ochre', 'aci': 2, 'label': '도로 코리더'},
    {'name': 'C-ROAD-SCTN', 'token': 'ink2', 'aci': 8, 'label': '횡단면 위치'},
    {'name': 'C-GRAD-PADS', 'token': 'blue', 'aci': 5, 'label': '부지 패드'},
    {'name': 'C-GRAD-DAYL', 'token': 'magenta', 'aci': 6, 'label': '사면 법면선'},
    {'name': 'C-GRAD-SLOP', 'token': 'magenta', 'aci': 6, 'label': '비탈면 표시'},
    {'name': 'C-GRAD-FEAT', 'token': 'green', 'aci': 3, 'label': '피처 라인'},
    {'name': 'C-ROAD-SWPT', 'token': 'orange', 'aci': 30, 'label': '주행 궤적'},
    {'name': 'V-PROP', 'token': 'ink2', 'aci': 7, 'label': '필지 경계'},
    {'name': 'V-PROP-TEXT', 'token': 'ink2', 'aci': 7, 'label': '필지 주기'},
    {'name': 'C-STRM-PIPE', 'token': 'blue', 'aci': 5, 'label': '우수 파이프'},
    {'name': 'C-STRM-STRC', 'token': 'blue', 'aci': 5, 'label': '우수 맨홀'},
    {'name': 'C-STRM-TEXT', 'token': 'blue', 'aci': 5, 'label': '관망 주기'},
    {'name': 'C-STRM-PROB', 'token': 'red', 'aci': 1, 'label': '관망 오류'},
]


def fixed(val, decimals=2):
    """소수점 포맷팅 헬퍼"""
    if val is None:
        return ""
    return f"{val:.{decimals}f}"


def format_station(sta, unit='ft', decimals=2):
    """측점(Station) 문자열 포맷팅 (예: 1+23.45)"""
    if sta is None:
        return ""
    k = 1000 if unit == 'm' else 100
    base = int(sta // k)
    rem = sta % k
    return f"{base}+{rem:05.2f}" if decimals == 2 else f"{base}+{int(rem):02d}"


def decimals_of(v):
    s = str(v)
    i = s.find('.')
    return 0 if i < 0 else min(3, len(s) - i - 1)


def centroid(pts):
    if not pts:
        return {'x': 0, 'y': 0}
    x_sum = sum(p['x'] for p in pts)
    y_sum = sum(p['y'] for p in pts)
    return {'x': x_sum / len(pts), 'y': y_sum / len(pts)}


def labels_along(pts, spacing, min_len):
    """다중선(Polyline)을 따라 일정 간격으로 주기 배치 위치 계산"""
    out = []
    total = 0.0
    for i in range(1, len(pts)):
        total += math.hypot(pts[i]['x'] - pts[i - 1]['x'], pts[i]['y'] - pts[i - 1]['y'])

    if total < min_len:
        return out

    n = max(1, math.floor(total / spacing))
    step = total / n
    want = step / 2.0
    acc = 0.0

    for i in range(1, len(pts)):
        if len(out) >= n:
            break
        a, b = pts[i - 1], pts[i]
        length = math.hypot(b['x'] - a['x'], b['y'] - a['y'])

        while acc + length >= want and len(out) < n:
            t = (want - acc) / length if length > 0 else 0
            rot = math.atan2(b['y'] - a['y'], b['x'] - a['x'])
            if rot > math.pi / 2:
                rot -= math.pi
            elif rot < -math.pi / 2:
                rot += math.pi
            out.append({
                'x': a['x'] + (b['x'] - a['x']) * t,
                'y': a['y'] + (b['y'] - a['y']) * t,
                'rot': rot
            })
            want += step
        acc += length

    return out


def plan_scene(state, opts=None):
    """
    프로젝트 상태(state)를 받아 평면 도면용 아이템 객체 목록을 생성
    """
    if opts is None:
        opts = {}

    mm_per_unit = opts.get('mmPerUnit', 1.0)
    show = opts.get('show', {})

    items = []
    u = state.get('units', 'ft')

    # 기본 표시 설정
    s_opts = {
        'triangles': False, 'contours': True, 'labels': True,
        'breaklines': True, 'outline': True, 'points': True,
        'pointLabels': False, 'slopes': False, 'alignments': True,
        'pads': True, 'pipes': True, 'pointLabelText': 'nzd'
    }
    s_opts.update(show)

    unit_per_mm = 1.0 / mm_per_unit if mm_per_unit > 0 else 1.0
    sf = state.get('surface')

    # 1. 삼각망(TIN) 렌더링
    if sf and s_opts['triangles'] and hasattr(sf, 'edges'):
        edges = sf.edges()
        X, Y = sf.X, sf.Y
        ox, oy = getattr(sf, 'ox', 0), getattr(sf, 'oy', 0)
        for i in range(0, len(edges), 2):
            items.append({
                'layer': 'C-TOPO-TINN', 'kind': 'poly',
                'pts': [
                    {'x': X[edges[i]] + ox, 'y': Y[edges[i]] + oy},
                    {'x': X[edges[i + 1]] + ox, 'y': Y[edges[i + 1]] + oy}
                ]
            })

    # 2. 외곽 경계
    if sf and s_opts['outline'] and hasattr(sf, 'outline'):
        for loop in sf.outline():
            items.append({'layer': 'C-TOPO-BNDY', 'kind': 'poly', 'pts': loop, 'closed': True})

    # 3. 등고선
    contours = state.get('contours', {})
    if sf and s_opts['contours'] and contours.get('list'):
        interval = contours.get('interval', 1.0)
        major_interval = interval * contours.get('major', 5)
        dec = decimals_of(interval)

        def is_major(z):
            return abs(z / major_interval - round(z / major_interval)) < 1e-6

        for c in contours['list']:
            maj = is_major(c['z'])
            items.append({
                'layer': 'C-TOPO-MAJR' if maj else 'C-TOPO-MINR',
                'kind': 'poly', 'pts': c['pts'], 'closed': c.get('closed', False),
                'elev': c['z']
            })
            if maj and s_opts['labels']:
                for lbl in labels_along(c['pts'], 60 * unit_per_mm, 25 * unit_per_mm):
                    items.append({
                        'layer': 'C-TOPO-TEXT', 'kind': 'text',
                        'x': lbl['x'], 'y': lbl['y'], 'rot': lbl['rot'],
                        'mm': 2.0, 'align': 'center', 'middle': True,
                        'text': fixed(c['z'], dec), 'mask': True
                    })

    # 4. 경사 화살표
    if sf and s_opts['slopes'] and hasattr(sf, 'slopes'):
        length = 4.0 * unit_per_mm
        for a in sf.slopes():
            if a['size'] < length * 0.8 or a['slope'] <= 1e-6:
                continue
            dx = math.cos(a['dir']) * length / 2.0
            dy = math.sin(a['dir']) * length / 2.0
            tip = {'x': a['x'] + dx, 'y': a['y'] + dy}
            h = length * 0.3
            ang = a['dir']

            items.append({'layer': 'C-TOPO-SLOP', 'kind': 'poly', 'pts': [{'x': a['x'] - dx, 'y': a['y'] - dy}, tip]})
            items.append({
                'layer': 'C-TOPO-SLOP', 'kind': 'poly',
                'pts': [
                    {'x': tip['x'] - math.cos(ang - 0.45) * h, 'y': tip['y'] - math.sin(ang - 0.45) * h},
                    tip,
                    {'x': tip['x'] - math.cos(ang + 0.45) * h, 'y': tip['y'] - math.sin(ang + 0.45) * h}
                ]
            })

    # 5. 브레이크라인
    if s_opts['breaklines']:
        for b in state.get('breaklines', []):
            items.append({'layer': 'C-TOPO-BRKL', 'kind': 'poly', 'pts': b['pts'], 'z': True})

    # 6. 측량 포인트
    if s_opts['points']:
        for p in state.get('points', []):
            items.append({'layer': 'V-NODE', 'kind': 'point', 'x': p['x'], 'y': p['y'], 'z': p.get('z') or 0})
            if s_opts['pointLabels']:
                lbl_text = p.get('n', '')
                if s_opts['pointLabelText'] != 'n' and p.get('z') is not None:
                    lbl_text += '  ' + fixed(p['z'], 2)
                if s_opts['pointLabelText'] == 'nzd' and p.get('d'):
                    lbl_text += '  ' + p['d']

                items.append({
                    'layer': 'V-NODE-TEXT', 'kind': 'text',
                    'x': p['x'] + 1.2 * unit_per_mm, 'y': p['y'] + 0.4 * unit_per_mm,
                    'rot': 0, 'mm': 1.5, 'align': 'left', 'text': lbl_text
                })

    # 7. 부지 패드 (Pads)
    if s_opts['pads']:
        for pd in state.get('pads', []):
            items.append({'layer': 'C-GRAD-PADS', 'kind': 'poly', 'pts': pd['pts'], 'closed': True, 'elev': pd['z']})
            if pd.get('daylight'):
                items.append({'layer': 'C-GRAD-DAYL', 'kind': 'poly', 'pts': pd['daylight'], 'closed': True, 'z': True})
                for r in pd.get('rays', []):
                    if r.get('d', 0) > 1e-6:
                        items.append({'layer': 'C-GRAD-SLOP', 'kind': 'poly',
                                      'pts': [{'x': r['x0'], 'y': r['y0']}, {'x': r['x'], 'y': r['y']}]})

            c = centroid(pd['pts'])
            items.append({
                'layer': 'C-GRAD-PADS', 'kind': 'text',
                'x': c['x'], 'y': c['y'], 'rot': 0, 'mm': 2.2,
                'align': 'center', 'middle': True,
                'text': f"{pd.get('name', '패드')} (EL: {fixed(pd['z'], 2)})", 'mask': True
            })

    # 8. 선형 (Alignments) 및 측점
    if s_opts['alignments']:
        for a in state.get('alignments', []):
            al = a.get('alignment')
            if not al or not getattr(al, 'ok', False):
                if len(a.get('pis', [])) >= 2:
                    items.append({'layer': 'C-ROAD-CNTR', 'kind': 'poly', 'pts': a['pis'], 'dashed': True})
                continue

            for e in al.elements:
                if e['type'] == 'line':
                    items.append({'layer': 'C-ROAD-CNTR', 'kind': 'poly', 'pts': [e['p0'], e['p1']]})
                else:
                    a1 = e['a0'] + (e['delta'] if e['ccw'] else -e['delta'])
                    items.append({
                        'layer': 'C-ROAD-CNTR', 'kind': 'arc',
                        'c': e['c'], 'r': e['r'],
                        'a0': e['a0'] if e['ccw'] else a1,
                        'a1': a1 if e['ccw'] else e['a0']
                    })

            # 측점 틱(Tick) 및 주법(Stationing)
            major_step = 100
            minor_step = 20 if u == 'm' else 50
            tick = 1.5 * unit_per_mm

            for t_item in al.ticks(minor_step):
                is_maj = abs(t_item['sta'] / major_step - round(t_item['sta'] / major_step)) < 1e-9
                nx = math.sin(t_item['dir'])
                ny = -math.cos(t_item['dir'])
                k_val = tick * 1.6 if is_maj else tick

                items.append({
                    'layer': 'C-ROAD-STAN', 'kind': 'poly',
                    'pts': [
                        {'x': t_item['x'] - nx * k_val, 'y': t_item['y'] - ny * k_val},
                        {'x': t_item['x'] + nx * k_val, 'y': t_item['y'] + ny * k_val}
                    ]
                })
                if is_maj:
                    rot = t_item['dir'] - math.pi / 2.0
                    off = -(k_val + 0.8 * unit_per_mm)
                    align_str = 'right'
                    if math.cos(rot) < -1e-9 or (abs(math.cos(rot)) <= 1e-9 and math.sin(rot) < 0):
                        rot += math.pi
                        align_str = 'left'
                    items.append({
                        'layer': 'C-ROAD-STAN', 'kind': 'text',
                        'x': t_item['x'] + nx * off, 'y': t_item['y'] + ny * off,
                        'rot': rot, 'mm': 1.8, 'align': align_str, 'middle': True,
                        'text': format_station(t_item['sta'], u, 0)
                    })

    return {'layers': LAYERS, 'items': items}


def to_dxf_entities(scene, mm_per_unit):
    """
    Scene 생성 아이템들을 DXF 파일 내보내기용 엔티티 구조로 변환
    """
    out = []
    for it in scene.get('items', []):
        kind = it['kind']
        if kind == 'poly':
            if it.get('z'):
                out.append(
                    {'type': 'poly3d', 'layer': it['layer'], 'pts': it['pts'], 'closed': it.get('closed', False)})
            else:
                out.append({'type': 'poly', 'layer': it['layer'], 'pts': it['pts'], 'closed': it.get('closed', False),
                            'elev': it.get('elev', 0)})
        elif kind == 'arc':
            out.append(
                {'type': 'arc', 'layer': it['layer'], 'c': it['c'], 'r': it['r'], 'a0': it['a0'], 'a1': it['a1']})
        elif kind == 'point':
            out.append({'type': 'point', 'layer': it['layer'], 'x': it['x'], 'y': it['y'], 'z': it['z']})
        elif kind == 'text':
            h = it['mm'] / mm_per_unit if mm_per_unit > 0 else it['mm']
            dx = math.sin(it['rot']) * h / 2.0 if it.get('middle') else 0
            dy = -math.cos(it['rot']) * h / 2.0 if it.get('middle') else 0
            out.append({
                'type': 'text', 'layer': it['layer'],
                'x': it['x'] + dx, 'y': it['y'] + dy, 'h': h,
                'rot': it['rot'], 'text': it['text'], 'align': it.get('align', 'left')
            })
    return out