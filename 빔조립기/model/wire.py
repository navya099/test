from line3d import Line3d


class WireData(Line3d):
    def __init__(self, name, start,end):
        super().__init__(start,end)
        self.name = name


