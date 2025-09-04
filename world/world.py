import pygame
import random
import numpy as np

from scipy.ndimage import label, binary_dilation


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
        logger.info("Filling world with water and creating mountains")
        for x in range(self.world_size_x):
            for y in range(self.world_size_y):
                tile = self.get_tile(x, y)
                h = self.height_map[x, y]
                if h < self.water_level:
                    tile.is_water = True
                    self.water_map[x, y] = 1
                elif h > self.ice_caps_level:
                    self.set_tile(x,y, Tile(terrain=TERRAIN_DATA["ice_cap"]))
                elif h > self.mountain_level:
                    self.set_tile(x,y, Tile(terrain=TERRAIN_DATA["mountain"]))

    def carve_rivers(self):
        """
        Generate a river from a random mountain tile.
        Rivers mouth is  located at:
        - the largest water cluster or
        - map edge
        using A* pathfinding over the height map. The river prefers downhill flow.
        """
        logger.debug("Generating river")
        # --- 1. Identify mountain tiles ---
        mountain_coords = [(x, y) for x in range(self.world_size)
                                for x in range(self.world_size)
                                if self.get_tile(x,y).terrain.name in ["mountain", "ice_cap"]]

        if not mountain_coords:
            return

        headwaters = random.choice(mountain_coords)
        logger.info(f"posible headwater fuond at: {headwaters}")

        # --- 2. Identify largest water cluster ---
        labeled_water, num_features = label(self.water_map)

        if num_features == 0:# Define edges as functions that return a coordinate
            logger.info("No water to flow into, placing river mouth at world edge.")
            edges = [
                lambda: [0, np.random.randint(0, self.world_size_y)],                    # top
                lambda: [self.world_size_x-1, np.random.randint(0, self.world_size_y)],  # bottom
                lambda: [np.random.randint(0, self.world_size_x), 0],                    # left
                lambda: [np.random.randint(0, self.world_size_x), self.world_size_y-1]   # right
            ]

            # Pick one at random
            river_mouth = np.array([np.random.choice(edges)()])  # call the selected lambda
        else:
            # Find largest water cluster
            sizes = [(labeled_water==i).sum() for i in range(1, num_features+1)]
            largest_cluster_label = np.argmax(sizes) + 1
            river_mouth = np.argwhere(labeled_water == largest_cluster_label)

        # Pick a random tile in the largest water cluster as the target
        river_mouth = tuple(random.choice(river_mouth))
        logger.info(f"River mouth set to {river_mouth}")

        # --- 3. Prepare height-based cost matrix ---
        cost_matrix = np.ones((self.world_size, self.world_size))
        noise = np.random.rand(self.world_size, self.world_size) * 9.5  # tweak factor to produce meandring
        cost_matrix += noise

        for y in range(self.world_size):
            for x in range(self.world_size):
                # Penalize tiles higher than current headwaters to prefer downhill
                cost_matrix[y, x] += max(0, self.height_map[y, x] - self.height_map[headwaters[0], headwaters[1]])

        # --- 4. Use pathfinding library ---
        grid = Grid(matrix=cost_matrix.tolist())
        start_node = grid.node(headwaters[1], headwaters[0])  # note: Grid uses (x,y)
        end_node = grid.node(end[1], end[0])

        finder = AStarFinder(diagonal_movement=True)  # allow diagonal river flow
        path, _ = finder.find_path(start_node, end_node, grid)

        if not path:
            print("Failed to find river path.")
            return

        # --- 5. Carve river into map ---
        for x, y in path:  # path returned as (x,y)
            if "water" not in self.get_tile(x,y).terrain.name:
                self.get_tile(x,y) =.name Tile("water_river")
                self.water_map[y][x] = 1


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