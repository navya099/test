def format_meter(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value)
