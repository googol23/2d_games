from terrain import Terrain, TERRAIN_DATA, load_terrains_data

class Tile:
    def __init__(self, is_water:bool=False, terrain: Terrain | None = None):
        self.is_water = is_water
        self.terrain = terrain

