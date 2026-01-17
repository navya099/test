import numpy as np
from core.bve.heightblock import HeightBlock

class TerrainGerator:
    @staticmethod
    def create_terrain(elevlist: np.ndarray) -> list[HeightBlock]:
        terrains = []
        for i, elev in enumerate(elevlist):
            pos = i * 25
            terrains.append(HeightBlock(sta=pos, height=elev))
        return terrains