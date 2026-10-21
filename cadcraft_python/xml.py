import re


class XmlError(Exception):
    """XML 파싱 중 발생하는 커스텀 예외"""
    pass


ENT = {'amp': '&', 'lt': '<', 'gt': '>', 'quot': '"', 'apos': "'"}


def decode(s):
    if '&' not in s:
        return s

    def replace_entity(match):
        e = match.group(1)
        if e.startswith('#'):
            try:
                cp = int(e[2:], 16) if e[1] == 'x' else int(e[1:], 10)
                return chr(cp)
            except Exception:
                return ''
        return ENT.get(e, match.group(0))

    return re.sub(r'&(#x[0-9a-fA-F]+|#\d+|[a-zA-Z]+);', replace_entity, s)


def local(n):
    i = n.find(':')
    return n if i < 0 else n[i + 1:]


def parse_xml(text, max_depth=256):
    s = str(text)
    i = 0
    root = {'name': '#doc', 'attrs': {}, 'children': [], 'text': ''}
    stack = [root]
    n = len(s)

    def append_text(el, t_val):
        if el['name'] != '#doc':
            el['text'] += decode(t_val)

    while i < n:
        lt = s.find('<', i)
        top = stack[-1]
        if lt < 0:
            append_text(top, s[i:])
            break
        if lt > i:
            append_text(top, s[i:lt])

        if s.startswith('<!--', lt):
            e = s.find('-->', lt + 4)
            if e < 0:
                raise XmlError("Unclosed comment")
            i = e + 3
            continue
        if s.startswith('<![CDATA[', lt):
            e = s.find(']]>', lt + 9)
            if e < 0:
                raise XmlError("Unclosed CDATA")
            top['text'] += s[lt + 9:e]
            i = e + 3
            continue
        if s.startswith('<?', lt):
            e = s.find('?>', lt + 2)
            if e < 0:
                raise XmlError("Unclosed processing instruction")
            i = e + 2
            continue
        if s.startswith('<!', lt):
            # DOCTYPE 및 내부 서브셋 처리
            j = lt + 2
            depth = 0
            while j < n:
                c = s[j]
                if c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                elif c == '>' and depth <= 0:
                    break
                j += 1
            i = j + 1
            continue

        if s[lt + 1] == '/':
            e = s.find('>', lt)
            if e < 0:
                raise XmlError("Unclosed end tag")
            name = local(s[lt + 2:e].strip())
            el = stack.pop() if stack else None
            if not el or el is root or el['name'] != name:
                raise XmlError(f"Mismatched end tag </{name}>")
            i = e + 1
            continue

        # 시작 태그(Start Tag) 파싱
        j = lt + 1
        while j < n and not re.match(r'[\s/>]', s[j]):
            j += 1
        el_name = local(s[lt + 1:j])
        el = {'name': el_name, 'attrs': {}, 'children': [], 'text': ''}
        if not el['name']:
            raise XmlError("Empty tag name")

        while True:
            while j < n and s[j].isspace():
                j += 1
            if j >= n:
                raise XmlError(f"Unclosed tag <{el['name']}>")
            if s[j] == '>':
                j += 1
                top['children'].append(el)
                stack.append(el)
                if len(stack) > max_depth:
                    raise XmlError("Maximum depth exceeded")
                break
            if s[j] == '/' and j + 1 < n and s[j + 1] == '>':
                j += 2
                top['children'].append(el)
                break

            k = j
            while k < n and not re.match(r'[\s=/>]', s[k]):
                k += 1
            an = s[j:k]
            while k < n and s[k].isspace():
                k += 1
            if k >= n or s[k] != '=':
                raise XmlError(f"Attribute value expected in <{el['name']}>")
            k += 1
            while k < n and s[k].isspace():
                k += 1
            if k >= n:
                raise XmlError(f"Attribute value expected in <{el['name']}>")
            q = s[k]
            if q != '"' and q != "'":
                raise XmlError(f"Unquoted attribute value in <{el['name']}>")
            e = s.find(q, k + 1)
            if e < 0:
                raise XmlError(f"Unclosed attribute value in <{el['name']}>")
            if not an.startswith('xmlns'):
                el['attrs'][local(an)] = decode(s[k + 1:e])
            j = e + 1
        i = j

    if len(stack) != 1:
        raise XmlError(f"Unclosed tag <{stack[-1]['name']}>")
    doc_el = root['children'][0] if root['children'] else None
    if not doc_el:
        raise XmlError("No document element found")
    return doc_el


def kids(el, name):
    return [c for c in el.get('children', []) if c.get('name') == name] if el else []


def kid(el, name):
    if not el:
        return None
    for c in el.get('children', []):
        if c.get('name') == name:
            return c
    return None


def text_of(el):
    return el.get('text', '').strip() if el else ''


# XML에서 허용되지 않는 제어 문자 제거 정규식
BAD_CHARS_RE = re.compile(r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\ufffe\uffff]')


def esc(s):
    if s is None:
        return ''
    s_str = BAD_CHARS_RE.sub('', str(s))
    return (s_str
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))