"""Symmetric parabolic vertical curves for the Railspan elevation profile."""
from dataclasses import dataclass


@dataclass(frozen=True)
class VerticalCurve:
    start: float
    end: float
    elevation: float
    incoming: float
    outgoing: float

    def at(self, station):
        distance = station - self.start
        change = self.outgoing - self.incoming
        return self.elevation + distance * (
            self.incoming + change * distance / (2 * (self.end - self.start))
        )

    def extremum(self):
        change = self.outgoing - self.incoming
        if change:
            ratio = -self.incoming / change
            if 0 < ratio < 1:
                return self.start + ratio * (self.end - self.start)
        return None
