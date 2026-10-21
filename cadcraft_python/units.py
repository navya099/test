import math
import re

UNITS = {
    'ft': {
        'key': 'ft', 'name': 'Feet', 'short': 'ft', 'area': 'sq ft', 'vol': 'cu yd', 'volPer': 27,
        'staLen': 100, 'staDec': 2, 'dec': 2, 'landxml': 'USSurveyFoot'
    },
    'm': {
        'key': 'm', 'name': 'Metres', 'short': 'm', 'area': 'sq m', 'vol': 'cu m', 'volPer': 1,
        'staLen': 1000, 'staDec': 3, 'dec': 3, 'landxml': 'meter'
    }
}


def unit_of(u):
    return UNITS.get(u, UNITS['ft'])


# 선형 단위별 미터 환산 계수 (LandXML linearUnit 이름 기준)
METRES_PER = {
    'USSurveyFoot': 1200 / 3937, 'foot': 0.3048, 'ft': 0.3048,
    'meter': 1, 'm': 1, 'metre': 1, 'millimeter': 0.001, 'centimeter': 0.01, 'kilometer': 1000
}


def format_station(sta, unit='ft', dec=None):
    if not (isinstance(sta, (int, float)) and math.isfinite(sta)):
        return ''
    u = unit_of(unit)
    d = dec if dec is not None else u['staDec']
    neg = sta < 0
    r = round(abs(sta), d)
    big = math.floor(r / u['staLen'] + 1e-9)
    rest = r - big * u['staLen']
    if rest < 0:
        rest = 0.0
    w = len(str(u['staLen'])) - 1
    rest_str = f"{rest:.{d}f}".zfill(w + (d + 1 if d > 0 else 0))
    return ('-' if neg else '') + str(big) + '+' + rest_str


def parse_station(s, unit='ft'):
    t_str = str(s if s is not None else '').strip()
    if not t_str:
        return None
    m = re.match(r'^([+-]?)(\d+)\+(\d+(?:\.\d*)?)$', t_str)
    if m:
        v = int(m.group(2)) * unit_of(unit)['staLen'] + float(m.group(3))
        return -v if m.group(1) == '-' else v
    return float(t_str) if is_num(t_str) else None


M_PER_IN = 0.0254


def one_length(x, unit):
    s = str(x).strip().lower()
    s = re.sub(r'\s+', ' ', s)
    if is_num(s):
        return float(s)

    def to_unit(metres):
        return metres if unit == 'm' else metres / M_PER_IN / 12

    m = re.match(r'^(\d+(?:\.\d*)?|\.\d+) ?(mm|cm|m)$', s)
    if m:
        val = float(m.group(1))
        unit_str = m.group(2)
        mult = 0.001 if unit_str == 'mm' else (0.01 if unit_str == 'cm' else 1.0)
        return to_unit(val * mult)

    def frac(q):
        f = re.match(r'^(?:(\d+)[ -])?(\d+)\/(\d+)$', q.strip())
        if f:
            if f.group(3) == '0':
                return None
            return float(f.group(1) or 0) + float(f.group(2)) / float(f.group(3))
        return float(q.strip()) if is_num(q.strip()) else None

    bare = frac(s)
    if bare is not None:
        return bare

    s = re.sub(r'\b(feet|foot|ft)\b\.?', "'", s)
    s = re.sub(r'\b(inches|inch|in)\b\.?', '"', s)
    s = s.replace("''", '"')

    fi = re.match(r"^(?:([\d./ -]+?) ?')?(?: ?-? ?([\d./ -]+?) ?\")?$", s)
    if not fi or (not fi.group(1) and not fi.group(2)):
        return None
    ft = frac(fi.group(1)) if fi.group(1) else 0.0
    inch = frac(fi.group(2)) if fi.group(2) else 0.0
    if ft is None or inch is None:
        return None
    feet = ft + inch / 12.0
    return feet * 12 * M_PER_IN if unit == 'm' else feet


def read_length(text, unit='ft'):
    s = str(text if text is not None else '').strip()
    s = re.sub(r"[′’‘`]", "'", s)
    s = re.sub(r"[″“”]", '"', s)
    s = re.sub(r"[−–—]", '-', s)
    s = s.replace(',', '')
    if not s:
        return {'ok': False, 'error': f"Invalid length: '{text}'"}

    sign = -1 if s.startswith('-') else 1
    clean_s = re.sub(r'^[+-]', '', s)
    v = one_length(clean_s, unit)
    if v is None:
        return {'ok': False, 'error': f"Invalid length: '{s}'"}
    return {'ok': True, 'value': sign * v}


def is_num(s):
    if isinstance(s, (int, float)):
        return math.isfinite(s)
    try:
        float(str(s).strip())
        return True
    except ValueError:
        return False


def fixed(n, d=2):
    if not (isinstance(n, (int, float)) and math.isfinite(n)):
        return ''
    v = 0 if abs(n) < 0.5 * (10 ** -d) else n
    return f"{v:.{d}f}"


def grouped(n, d=0):
    if not (isinstance(n, (int, float)) and math.isfinite(n)):
        return ''
    formatter = f"{{:,.{d}f}}"
    return formatter.format(n)


def pct(g, d=2):
    if isinstance(g, (int, float)) and math.isfinite(g):
        val = g * 100
        prefix = '+' if val >= 0 else ''
        return prefix + fixed(val, d) + '%'
    return ''


def volume_text(v, unit='ft', d=1):
    u = unit_of(unit)
    return grouped(v / u['volPer'], d) + ' ' + u['vol']


def area_text(a, unit='ft', d=0):
    return grouped(a, d) + ' ' + unit_of(unit)['area']


def bearing(a):
    az = (90 - a * 180 / math.pi) % 360
    if az < 0:
        az += 360
    if az <= 90:
        q = ('N', 'E');
        ang = az
    elif az <= 180:
        q = ('S', 'E');
        ang = 180 - az
    elif az <= 270:
        q = ('S', 'W');
        ang = az - 180
    else:
        q = ('N', 'W');
        ang = 360 - az
    return q[0] + ' ' + dms(ang) + ' ' + q[1]


def dms(deg):
    s = round(abs(deg) * 3600)
    d = s // 3600
    s -= d * 3600
    m = s // 60
    s -= m * 60
    return f"{d}°{str(m).zfill(2)}'{str(s).zfill(2)}\""