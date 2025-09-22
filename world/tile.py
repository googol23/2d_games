import pygame
from terrain import Terrain, TERRAIN_DATA, load_terrains_data
from dataclasses import dataclass

# @dataclass(slots=True)
class Tile(pygame.sprite.Sprite):
    def __init__(self,is_water:bool = False, terrain:Terrain | None = None):
        super().__init__()

        self.terrain = terrain

        # TODO Handle later as property
        self.is_water = is_water 
# FUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUCCCCCCCCCCCCCCCCCCCCCCCCCCCCCKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKkk