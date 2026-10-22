# project.py
import json
from datetime import datetime

# 기본 디스플레이 설정값 정의
DISPLAY_DEFAULTS = {
    'surface': 'eg', 'triangles': False, 'contours': True, 'interval': 1,
    'major': 5, 'labels': True, 'bands': False, 'bandCount': 8,
    'slopes': False, 'points': True, 'pointLabels': False,
    'breaklines': True, 'outline': True, 'pipes': True,
    'profFeatures': True, 'profWithin': 0, 'gradeOverlay': False
}

MAX_UNDO = 200


def empty_state():
    """초기 프로젝트 상태 객체 생성"""
    return {
        'name': '제목 없음', 'units': 'ft',
        'surface': {
            'name': '원지반', 'groups': {}, 'breaklines': [],
            'boundary': None, 'maxEdge': 0, 'tin': None,
            'descKeys': [], 'lineCodes': {}
        },
        'display': {**DISPLAY_DEFAULTS},
        'alignments': [], 'pads': [], 'network': None,
        'seq': 1, 'crs': None, 'features': [], 'parcels': [],
        'gis': {'layers': [], 'maps': []}
    }


class Project:
    def __init__(self):
        self.state = empty_state()
        self.points = []
        self.points_file = ''
        self.points_version = 0
        self.gis_features = {}  # GIS 레이어 데이터 맵
        self.undo_stack = []
        self.redo_stack = []
        self.version = 0
        self.saved = 0
        self.cache = {}
        self.listeners = set()

    def on(self, f):
        """상태 변경 리스너 등록"""
        self.listeners.add(f)
        return lambda: self.listeners.remove(f)

    def emit(self, kind):
        """리스너 이벤트 발생"""
        for f in self.listeners:
            f(kind)

    @property
    def dirty(self):
        """저장되지 않은 변경 사항이 있는지 확인"""
        return self.version != self.saved

    def snapshot(self):
        """현재 상태의 JSON 스냅샷 생성 (TIN 및 디스플레이 제외)"""
        surf = {k: v for k, v in self.state['surface'].items() if k != 'tin'}
        rest = {k: v for k, v in self.state.items() if k != 'display'}
        return json.dumps({**rest, 'surface': surf})

    def restore(self, json_str):
        """스냅샷 JSON으로부터 상태 복원"""
        s = json.loads(json_str)
        s['surface']['tin'] = self.state['surface'].get('tin')
        s['display'] = self.state['display']
        self.state = s

    def set_display(self, k, v):
        """디스플레이 설정 변경 (Undo 대상 아님)"""
        if self.state['display'].get(k) == v:
            return
        self.state['display'][k] = v
        self.touch('display')

    def change(self, label, fn):
        """상태 변경을 하나의 Undo 단계로 기록"""
        before = self.snapshot()
        fn(self.state)
        if self.snapshot() == before:
            return False

        self.undo_stack.append({'label': label, 'json': before})
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)
        self.redo_stack = []
        self.touch('change')
        return True

    def step(self, from_stack, to_stack, kind):
        """Undo 또는 Redo 수행"""
        if not from_stack:
            return None
        u = from_stack.pop()
        to_stack.append({'label': u['label'], 'json': self.snapshot()})
        self.restore(u['json'])
        self.touch(kind)
        return u['label']

    def undo(self):
        return self.step(self.undo_stack, self.redo_stack, 'undo')

    def redo(self):
        return self.step(self.redo_stack, self.undo_stack, 'redo')

    def touch(self, kind):
        """버전 증가 및 변경 알림 발생"""
        self.version += 1
        self.emit(kind)

    def next_id(self, prefix):
        """고유 ID 생성기"""
        seq = self.state['seq']
        self.state['seq'] += 1
        return f"{prefix}{seq}"

    def set_points(self, points, file=''):
        """측량 포인트 설정"""
        self.points = points
        self.points_file = file
        self.points_version += 1
        self.undo_stack = []
        self.redo_stack = []
        self.touch('points')

    def to_json(self):
        """프로젝트 파일을 위한 JSON 데이터 변환"""
        return {
            'format': 'civilcraft-project',
            'version': 1,
            'saved': datetime.now().isoformat(),
            'name': self.state['name'],
            'units': self.state['units'],
            'pointsFile': self.points_file,
            'points': [[p.get('n'), p['x'], p['y'], p.get('z'), p.get('d', '')] for p in self.points],
            'surface': self.state['surface'],
            'display': self.state['display'],
            'alignments': self.state['alignments'],
            'pads': self.state['pads'],
            'network': self.state['network'],
            'seq': self.state['seq'],
            'features': self.state.get('features', []),
            'parcels': self.state.get('parcels', []),
            'crs': self.state['crs']
        }