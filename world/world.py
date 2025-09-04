import pygame
import random
import numpy as np

from .tile import Tile
from terrain import TERRAIN_DATA, Terrain, load_terrains_data
from rendering import Camera
from .topology import generate_topological_map

import logging
logger = logging.getLogger(__name__)

class World:
    def __init__(self, world_size_x: int, world_size_y: int):
        self.world_size_x = world_size_x
        self.world_size_y = world_size_y
        self.height_map = None

        # Pre-allocate tiles in a flat list
        logger.info("Creating new World ...")
        logger.info(" ... generating world tiles")
        size = world_size_x * world_size_y
        self.tiles = [Tile() for _ in range(size)]

    def __str__(self):
        return f"World: size_x = {self.world_size_x}, size_y = {self.world_size_y}"

    def generate(self):
        load_terrains_data()

        n_of_peaks = random.randint(10,100)
        self.height_map = generate_topological_map(self.world_size_x, self.world_size_y, n_of_peaks=n_of_peaks)

        self.water_level    = 0.3
        self.mountain_level = 0.80
        self.ice_caps_level = 0.95

        # Create a binary map: 1 for water, 0 otherwise
        self.water_map = np.zeros(shape=(self.world_size_x,self.world_size_y))

        # Mark tiles as water if below cutoff
        for x in range(self.world_size_x):
            for y in range(self.world_size_y):
                tile = self.get_tile(x, y)
                h = self.height_map[x, y]
                if h < self.water_level:
                    tile.is_water = True
                    self.water_map[x, y] = 1
                elif h > self.mountain_level:
                    self.set_tile(x,y, Tile(terrain=TERRAIN_DATA["mountain"]))
                if h > self.ice_caps_level:
                    self.set_tile(x,y, Tile(terrain=TERRAIN_DATA["ice_cap"]))


    def get_tile(self, x, y):
        return self.tiles[y * self.world_size_x + x]

    def set_tile(self, x, y, tile):
        self.tiles[y * self.world_size_x + x] = tile

    def render(self, surface: pygame.Surface, camera: Camera):
        tile_size = camera.tile_size

        # Cull: compute visible bounds once
        start_x = max(camera.x // tile_size, 0)
        end_x   = min((camera.x + camera.width) // tile_size + 1, self.world_size_x)
        start_y = max(camera.y // tile_size, 0)
        end_y   = min((camera.y + camera.height) // tile_size + 1, self.world_size_y)

        # Loop only over visible tiles
        for y in range(start_y, end_y):
            row_offset = y * self.world_size_x
            screen_y = y * tile_size - camera.y
            for x in range(start_x, end_x):
                tile = self.tiles[row_offset + x]
                screen_x = x * tile_size - camera.x

                if tile.terrain:
                    if tile.terrain.texture:
                        surface.blit(
                            pygame.transform.scale(tile.terrain.texture, (tile_size, tile_size)),
                            (screen_x, screen_y),
                        )
                    else:
                        pygame.draw.rect(
                            surface,
                            tile.terrain.color,
                            pygame.Rect(screen_x, screen_y, tile_size, tile_size),
                        )
                else:
                       pygame.draw.rect(
                            surface,
                            (87,87,87),
                            pygame.Rect(screen_x, screen_y, tile_size, tile_size),
                        )
        return surface