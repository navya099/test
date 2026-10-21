import math


class Thinner:
    def __init__(self, cell, mode='nearest', origin=(0, 0), classes=None, region=None, max_points=float('inf')):
        if not (cell > 0) or not math.isfinite(cell):
            raise ValueError("Invalid thinning cell spacing.")
        if mode not in ['lowest', 'nearest', 'average']:
            raise ValueError(f"Unknown thinning mode: {mode}")

        self.cell = cell
        self.mode = mode
        self.ox = origin[0]
        self.oy = origin[1]
        self.classes = classes  # set or None
        self.region = region  # {minX, minY, maxX, maxY} or None
        self.max = max_points

        self.map = {}
        self.cap = 1024
        self.X = [0.0] * self.cap
        self.Y = [0.0] * self.cap
        self.Z = [0.0] * self.cap
        self.W = [0.0] * self.cap

        self.count = 0
        self.seen = 0
        self.filtered = 0
        self.outside = 0
        self.capped = False
        self.dropped = 0

    def grow(self):
        n = self.cap * 2
        self.X.extend([0.0] * (n - self.cap))
        self.Y.extend([0.0] * (n - self.cap))
        self.Z.extend([0.0] * (n - self.cap))
        self.W.extend([0.0] * (n - self.cap))
        self.cap = n

    def add(self, x, y, z, cls):
        self.seen += 1
        if self.classes is not None and cls not in self.classes:
            self.filtered += 1
            return False

        r = self.region
        if r and (x < r['minX'] or x > r['maxX'] or y < r['minY'] or y > r['maxY']):
            self.outside += 1
            return False

        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            return False

        fx = (x - self.ox) / self.cell
        fy = (y - self.oy) / self.cell
        ix = math.floor(fx)
        iy = math.floor(fy)

        if abs(ix) >= 2097152 or abs(iy) >= 2147483647:
            self.outside += 1
            return False

        key = ix * 4294967296 + (iy + 2147483648)
        k = self.map.get(key)

        if k is None:
            if self.count >= self.max:
                self.capped = True
                self.dropped += 1
                return False
            k = self.count
            self.count += 1
            if k >= self.cap:
                self.grow()
            self.map[key] = k
            self.X[k] = x
            self.Y[k] = y
            self.Z[k] = z

            if self.mode == 'average':
                self.W[k] = 1.0
            elif self.mode == 'nearest':
                self.W[k] = (fx - ix - 0.5) ** 2 + (fy - iy - 0.5) ** 2
            else:
                self.W[k] = 0.0
            return True

        if self.mode == 'lowest':
            if z < self.Z[k]:
                self.X[k] = x
                self.Y[k] = y
                self.Z[k] = z
        elif self.mode == 'nearest':
            d = (fx - ix - 0.5) ** 2 + (fy - iy - 0.5) ** 2
            if d < self.W[k]:
                self.X[k] = x
                self.Y[k] = y
                self.Z[k] = z
                self.W[k] = d
        else:
            self.X[k] += x
            self.Y[k] += y
            self.Z[k] += z
            self.W[k] += 1.0
        return True

    def points(self):
        out = []
        avg = (self.mode == 'average')
        for k in range(self.count):
            if avg:
                w = self.W[k]
                out.append({'x': self.X[k] / w, 'y': self.Y[k] / w, 'z': self.Z[k] / w})
            else:
                out.append({'x': self.X[k], 'y': self.Y[k], 'z': self.Z[k]})
        return out


def grid_step(spacing, cell_size):
    if spacing > 0 and cell_size > 0:
        return max(1, round(spacing / cell_size))
    return 1


class Coverage:
    def __init__(self, box, n=128):
        self.box = box
        self.n = n
        self.w = max(box['maxX'] - box['minX'], 1e-9) / n
        self.h = max(box['maxY'] - box['minY'], 1e-9) / n
        self.by_class = {}
        self.counts = {}
        self.total = 0

    def add(self, x, y, cls):
        i = min(self.n - 1, max(0, math.floor((x - self.box['minX']) / self.w)))
        j = min(self.n - 1, max(0, math.floor((y - self.box['minY']) / self.h)))

        if cls not in self.by_class:
            self.by_class[cls] = [0] * (self.n * self.n)
        self.by_class[cls][j * self.n + i] += 1

        self.counts[cls] = self.counts.get(cls, 0) + 1
        self.total += 1

    def estimate(self, spacing, classes=None, box=None):
        n = self.n
        per = [0.0] * (n * n)
        for c, a in self.by_class.items():
            if classes is None or c in classes:
                for k in range(len(a)):
                    per[k] += a[k]

        keep = 0.0
        in_area = 0.0
        cell_area = self.w * self.h

        for j in range(n):
            for i in range(n):
                v = per[j * n + i]
                if not v:
                    continue
                f = 1.0
                if box:
                    x0 = self.box['minX'] + i * self.w
                    y0 = self.box['minY'] + j * self.h
                    ox = max(0.0, min(box['maxX'], x0 + self.w) - max(box['minX'], x0))
                    oy = max(0.0, min(box['maxY'], y0 + self.h) - max(box['minY'], y0))
                    f = (ox * oy) / cell_area
                    if not f:
                        continue
                in_area += v * f
                keep += min(v * f, (cell_area * f) / (spacing * spacing) + 1.0)

        return {'points': round(keep), 'inArea': round(in_area)}