"""Constant-radius alignment and polygonal envelopes in the start tangent frame."""

from bisect import bisect_right
import math

DEFAULTS = {"curve_radius": 0, "cant_mm": 0}


def bounds(vertices):
    axes = tuple(zip(*vertices))
    return [min(axis) for axis in axes], [max(axis) for axis in axes]


class StationProfile:
    def __init__(self, points, fallback, curves=()):
        self.points = tuple(points)
        self.stations = tuple(station for station, _ in self.points)
        self.fallback = fallback
        self.curves = tuple(curves)
        self.curve_starts = tuple(curve.start for curve in self.curves)
        self.breakpoints = tuple(sorted({
            *self.stations,
            *(s for curve in self.curves for s in (curve.start, curve.end, curve.extremum()) if s is not None),
        }))

    def at(self, station):
        if not self.points:
            return self.fallback
        curve_index = bisect_right(self.curve_starts, station) - 1
        if curve_index >= 0 and station <= self.curves[curve_index].end:
            return self.curves[curve_index].at(station)
        index = bisect_right(self.stations, station)
        if index == 0:
            return self.points[0][1]
        if index == len(self.points):
            return self.points[-1][1]
        a, za = self.points[index - 1]
        b, zb = self.points[index]
        return za + (zb - za) * (station - a) / (b - a)


class Alignment:
    def __init__(self, start, radius, cant_mm, deck, profile=(), curves=(), *, cant_profile=()):
        self.start = start
        self.center_offset = -radius  # Positive Y points left in the tangent frame.
        self.deck = deck
        self.profile = StationProfile(profile, deck, curves)
        self.cant = StationProfile(cant_profile, cant_mm)

    def roll_at(self, station):
        if not self.center_offset:
            return 0.0
        return math.copysign(math.atan2(self.cant.at(station), 1435), -self.center_offset)

    def elevation_at(self, station):
        return self.profile.at(station)

    def point(self, vertex, track_center=None, *, follow_profile=True):
        station, offset, z = vertex
        if track_center is not None and self.center_offset:
            roll = self.roll_at(station)
            cosine, sine = math.cos(roll), math.sin(roll)
            y, height = offset - track_center, z - self.deck
            offset = track_center + y * cosine - height * sine
            z = self.deck + y * sine + height * cosine
        if follow_profile and self.profile.points:
            z += self.elevation_at(station) - self.deck
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

    def cells(self, item, track_center, *, follow_profile):
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
        fractions = [1.0]
        if not item.get("chord"):
            if self.center_offset or follow_profile and self.profile.points:
                count = max(1, math.ceil(abs(last - first) / 5))
                fractions = [step / count for step in range(1, count + 1)]
            stations = self.profile.breakpoints if follow_profile else ()
            if track_center is not None and self.center_offset:
                stations += self.cant.breakpoints
            if stations and last != first:
                breaks = set(fractions)
                for a, b in zip(section(0), section(1)):
                    low, high = sorted((a[0], b[0]))
                    breaks.update((station - a[0]) / (b[0] - a[0])
                                  for station in stations if low < station < high)
                fractions = sorted(breaks)

        def mapped(t):
            return [self.point(vertex, track_center, follow_profile=follow_profile)
                    for vertex in section(t)]

        previous = mapped(0)
        for t in fractions:
            current = mapped(t)
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
