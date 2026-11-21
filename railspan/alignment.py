"""Constant-radius alignment and polygonal envelopes in the start tangent frame."""

import math

DEFAULTS = {"curve_radius": 0, "cant_mm": 0}


def bounds(vertices):
    axes = tuple(zip(*vertices))
    return [min(axis) for axis in axes], [max(axis) for axis in axes]


class Alignment:
    def __init__(self, start, radius, cant_mm, deck):
        self.start = start
        self.center_offset = -radius  # Positive Y points left in the tangent frame.
        self.deck = deck
        self.roll = math.copysign(math.atan2(cant_mm, 1435), radius) if radius else 0.0

    def point(self, vertex, track_center=None):
        station, offset, z = vertex
        if track_center is not None:
            y, height = offset - track_center, z - self.deck
            offset = track_center + y * math.cos(self.roll) - height * math.sin(self.roll)
            z = self.deck + y * math.sin(self.roll) + height * math.cos(self.roll)
        if not self.center_offset:
            return [station, offset, z]
        angle = (station - self.start) / self.center_offset
        return [
            self.start + (self.center_offset - offset) * math.sin(angle),
            2 * self.center_offset * math.sin(angle / 2) ** 2 + offset * math.cos(angle),
            z,
        ]

    def station_at(self, vertex):
        x, y, _ = vertex
        if not self.center_offset:
            return x
        return self.start + self.center_offset * math.atan2(
            (x - self.start) / self.center_offset, 1 - y / self.center_offset
        )

    def cells(self, item, track_center):
        """Return ordered solid mesh segments and their world-space bounds."""
        lo, hi = item["min"], item["max"]
        axis = item.get("axis")
        if axis:
            a, b = axis
            dx, dz = b[0] - a[0], b[2] - a[2]
            length = math.hypot(dx, dz)
            radius = item["thickness"] / 2

            def section(t):
                x, y, z = (v + (w - v) * t for v, w in zip(a, b))
                return [[x - dz / length * h, y + side, z + dx / length * h]
                        for side in (-radius, radius) for h in (-radius, radius)]

            first, last = a[0], b[0]
        else:
            first, last = lo[0], hi[0]

            def section(t):
                return [[first + (last - first) * t, y, z]
                        for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]

        # A stay is a straight chord between its two mapped anchors.
        count = max(1, math.ceil(abs(last - first) / 5)) if self.center_offset and not item.get("chord") else 1
        previous = [self.point(vertex, track_center) for vertex in section(0)]
        for step in range(1, count + 1):
            t = step / count
            current = [self.point(vertex, track_center) for vertex in section(t)]
            vertices = previous + current
            low, high = bounds(vertices)
            yield low, high, vertices
            previous = current


def separation(lo, hi, target_lo, target_hi):
    gap = max(a - d for a, d in zip(lo, target_hi))
    gap = max(gap, max(c - b for c, b in zip(target_lo, hi)))
    if gap <= 0:
        return gap
    return math.hypot(*(max(a - d, c - b, 0)
                        for a, b, c, d in zip(lo, hi, target_lo, target_hi)))
