from dataclasses import fields, is_dataclass
from enum import Enum
import inspect


def dump_api(obj, *, show_source: bool = False, source_lines: int | None = None):
    cls = obj if inspect.isclass(obj) else type(obj)
    doc = inspect.getdoc(cls)

    print(f"=== {cls.__module__}.{cls.__qualname__} ===")
    if not inspect.isclass(obj):
        print(f"  (instance of {cls.__qualname__})")
    if doc:
        print(doc)

    # 1) Enum 멤버
    if issubclass(cls, Enum):
        print("  [Enum members]")
        for member in cls:
            print(f"    {member.name} = {member.value!r}")

    # 2) Dataclass 필드
    if is_dataclass(cls):
        print("  [Dataclass fields]")
        for f in fields(cls):
            default_repr = (
                f"default={f.default!r}"
                if f.default is not f.default_factory
                else f"default_factory={getattr(f.default_factory, '__name__', f.default_factory)}"
            )
            print(f"    {f.name}: {f.type} ({default_repr})")

    # 3) 공개 메서드 / 프로퍼티 / 속성
    methods = []
    attrs = []
    for name, member in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        if inspect.isfunction(member) or inspect.ismethod(member) or isinstance(member, (classmethod, staticmethod)):
            func = member.__func__ if isinstance(member, (classmethod, staticmethod)) else member
            try:
                sig = str(inspect.signature(func))
            except ValueError:
                sig = "(...)"
            kind = "classmethod" if isinstance(member, classmethod) else "staticmethod" if isinstance(member, staticmethod) else "def"
            first_line = (inspect.getdoc(func) or "").splitlines()[0] if inspect.getdoc(func) else ""
            methods.append(f"    [{kind}] {name}{sig}" + (f"  # {first_line}" if first_line else ""))
        elif isinstance(member, property):
            attrs.append(f"    {name} (property)")
        elif not inspect.isclass(member) and not inspect.ismodule(member):
            attrs.append(f"    {name} ({type(member).__name__})")

    if attrs:
        print("  [Attributes / Properties]")
        print("\n".join(attrs))
    if methods:
        print("  [Methods]")
        print("\n".join(methods))

    # 4) 소스 코드 (선택)
    if show_source:
        print("  [Source]")
        try:
            src = inspect.getsource(cls)
            if source_lines is not None:
                src = "\n".join(src.splitlines()[:source_lines]) + "\n    ... (truncated)"
            print(src)
        except OSError as exc:
            print(f"    (source unavailable: {exc})")