def slope(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx = b[0] - a[0]
    if dx <= 0:
        raise ValueError(f"측점은 엄격하게 증가해야 합니다: {a[0]} → {b[0]}")
    return (b[1] - a[1]) / dx * 1000.0