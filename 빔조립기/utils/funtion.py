def format_meter(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value)

def try_parse_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def try_parse_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default