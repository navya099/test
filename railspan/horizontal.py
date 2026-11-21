"""Tangent-connected straight, circular and clothoid sections."""
from dataclasses import dataclass
import math

# Positive abscissas and weights for eight-point Gauss–Legendre integration.
GAUSS_NODES = (
    (.1834346424956498, .3626837833783620),
    (.5255324099163290, .3137066458778873),
    (.7966664774136267, .2223810344533745),
    (.9602898564975363, .1012285362903763),
)


def curvature(radius):
    return -1 / radius if radius else 0.0


def arc_displacement(distance, center, offset=0):
    turn = distance / center if center else 0
    forward = (center - offset) * math.sin(turn) if center else distance
    lateral = 2 * center * math.sin(turn / 2) ** 2 + offset * math.cos(turn)
    return forward, lateral, turn


@dataclass(frozen=True)
class PlanSegment:
    start: float
    end: float
    radius: float
    end_radius: float
    x: float
    y: float
    heading: float

    @property
    def transition(self):
        return self.radius != self.end_radius

    @property
    def direction(self):
        radius = self.radius or self.end_radius
        return (radius > 0) - (radius < 0)

    def curvature_at(self, station):
        if station <= self.start or not self.transition:
            return curvature(self.radius)
        if station >= self.end:
            return curvature(self.end_radius)
        fraction = (station - self.start) / (self.end - self.start)
        return curvature(self.radius) * (1 - fraction) + curvature(self.end_radius) * fraction

    def transition_displacement(self, distance, offset):
        length = self.end - self.start
        if distance <= 0:
            return arc_displacement(distance, -self.radius, offset)
        step = min(distance, length)
        incoming = curvature(self.radius)
        rate = (curvature(self.end_radius) - incoming) / length

        def angle(s):
            return s * (incoming + rate * s / 2)

        half = step / 2
        forward = lateral = 0.0
        for node, weight in GAUSS_NODES:
            before, after = angle(half * (1 - node)), angle(half * (1 + node))
            forward += weight * (math.cos(before) + math.cos(after))
            lateral += weight * (math.sin(before) + math.sin(after))
        turn = angle(step)
        dx, dy, extra_turn = arc_displacement(distance - step, -self.end_radius, offset)
        cosine, sine = math.cos(turn), math.sin(turn)
        return (forward * half + dx * cosine - dy * sine,
                lateral * half + dx * sine + dy * cosine, turn + extra_turn)

    def frame(self, station, offset=0):
        distance = station - self.start
        if self.transition:
            forward, lateral, turn = self.transition_displacement(distance, offset)
        else:
            forward, lateral, turn = arc_displacement(distance, -self.radius, offset)
        cosine, sine = math.cos(self.heading), math.sin(self.heading)
        return (self.x + forward * cosine - lateral * sine,
                self.y + forward * sine + lateral * cosine, self.heading + turn)

    def nearest(self, x, y):
        def score(station):
            px, py, _ = self.frame(station)
            return math.hypot(px - x, py - y), station

        if self.transition:
            samples = [self.start + (self.end - self.start) * i / 8 for i in range(9)]
            scores = list(map(score, samples))
            index = min(range(len(scores)), key=scores.__getitem__)
            lo, hi = samples[max(0, index - 1)], samples[min(8, index + 1)]
            for _ in range(42):
                a = lo + (hi - lo) / 3
                b = hi - (hi - lo) / 3
                if score(a) < score(b):
                    hi = b
                else:
                    lo = a
            return min(scores[index], score((lo + hi) / 2))

        dx, dy = x - self.x, y - self.y
        cosine, sine = math.cos(self.heading), math.sin(self.heading)
        forward = dx * cosine + dy * sine
        lateral = -dx * sine + dy * cosine
        center = -self.radius
        distance = center * math.atan2(forward / center, 1 - lateral / center) if center else forward
        station = self.start + distance
        candidates = (station,) if self.start <= station <= self.end else (self.start, self.end)
        return min(map(score, candidates))


def build_plan(start, rows):
    x, y, heading = start, 0, 0
    segments = []
    for end, radius, *trailing in rows:
        end_radius = trailing[0] if trailing else radius
        segment = PlanSegment(start, end, radius, end_radius, x, y, heading)
        segments.append(segment)
        x, y, heading = segment.frame(end)
        start = end
    return segments
