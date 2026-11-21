"""Tangent-connected straight and circular sections in local coordinates."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PlanSegment:
    start: float
    end: float
    radius: float
    x: float
    y: float
    heading: float

    def frame(self, station, offset=0):
        distance = station - self.start
        center = -self.radius
        cosine, sine = math.cos(self.heading), math.sin(self.heading)
        turn = distance / center if center else 0
        forward = (center - offset) * math.sin(turn) if center else distance
        lateral = 2 * center * math.sin(turn / 2) ** 2 + offset * math.cos(turn)
        return (self.x + forward * cosine - lateral * sine,
                self.y + forward * sine + lateral * cosine, self.heading + turn)

    def nearest(self, x, y):
        dx, dy = x - self.x, y - self.y
        cosine, sine = math.cos(self.heading), math.sin(self.heading)
        forward = dx * cosine + dy * sine
        lateral = -dx * sine + dy * cosine
        center = -self.radius
        distance = center * math.atan2(forward / center, 1 - lateral / center) if center else forward
        station = self.start + distance
        candidates = (station,) if self.start <= station <= self.end else (self.start, self.end)
        def score(candidate):
            px, py, _ = self.frame(candidate)
            return math.hypot(px - x, py - y), candidate
        return min(map(score, candidates))


def build_plan(start, rows):
    x, y, heading = start, 0, 0
    segments = []
    for end, radius in rows:
        segment = PlanSegment(start, end, radius, x, y, heading)
        segments.append(segment)
        x, y, heading = segment.frame(end)
        start = end
    return segments
