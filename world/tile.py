from terrain import Terrain, TERRAIN_DATA, load_terrains_data
from dataclasses import dataclass

@dataclass(slots=True)
class Tile:
    terrain:Terrain | None = None

    # TODO Handle later as property
    is_water:bool = False
