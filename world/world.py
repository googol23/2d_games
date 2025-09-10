import pygame
import random
import numpy as np
from collections import deque

from scipy.ndimage import label
from .tile import Tile
from terrain import TERRAIN_DATA, load_terrains_data
from rendering import Camera
from .topology import generate_topological_map, visualize_topological_map

import logging

logger = logging.getLogger(__name__)


class World:
    """
    Represents the game world, responsible for generation and rendering.
    """

    def __init__(self, world_size_x: int, world_size_y: int):
        self.world_size_x = world_size_x
        self.world_size_y = world_size_y
        self.height_map = None
        self.higest_peak:float = 1000

        logger.info("Creating new World ...")
        logger.info(" ... pre-allocating world tiles")
        size = world_size_x * world_size_y
        self.tiles = [Tile() for _ in range(size)]
        self.obstacle_map = np.zeros((self.world_size_y, self.world_size_x), dtype=bool)

    def generate_obstacles(self, density: float = 0.05, seed: int | None = None):
        """
        Generate random obstacles.
        density: fraction of tiles to block [0..1].
        seed: random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)

        self.obstacle_map = np.zeros((self.world_size_y, self.world_size_x), dtype=bool)
        num_obstacles = int(self.world_size_x * self.world_size_y * density)
        for _ in range(num_obstacles):
            x = random.randint(0, self.world_size_x - 1)
            y = random.randint(0, self.world_size_y - 1)
            self.obstacle_map[y, x] = True

    def get_tile(self, x: int, y: int) -> Tile:
        """Retrieves a tile at the given coordinates."""
        if 0 <= x < self.world_size_x and 0 <= y < self.world_size_y:
            return self.tiles[y * self.world_size_x + x]
        raise IndexError("Tile coordinates out of bounds")

    def set_tile(self, x: int, y: int, tile: Tile):
        """Sets a tile at the given coordinates."""
        if 0 <= x < self.world_size_x and 0 <= y < self.world_size_y:
            self.tiles[y * self.world_size_x + x] = tile
        else:
            raise IndexError("Tile coordinates out of bounds")

    def __str__(self):
        return f"World: size_x = {self.world_size_x}, size_y = {self.world_size_y}"

    def generate(self):
        """
        Generates the height map and assigns terrains based on height.
        """
        load_terrains_data()

        n_of_peaks = random.randint(5, 10)
        self.height_map = generate_topological_map(
            self.world_size_x, self.world_size_y, n_of_peaks=n_of_peaks
        )
        visualize_topological_map(self.height_map)

        water_ratio = 0.1  # 30% of tiles will be water
        mountain_ratio = 0.15  # top 15% are mountains
        ice_cap_ratio = 0.05  # top 5% are ice

        # Compute thresholds from height distribution
        flat_heights = self.height_map.flatten()
        self.water_level = np.percentile(flat_heights, water_ratio * 100)
        self.mountain_level = np.percentile(flat_heights, (1 - mountain_ratio) * 100)
        self.ice_caps_level = np.percentile(flat_heights, (1 - ice_cap_ratio) * 100)

        logger.info("Filling world with terrains based on height map")
        for y in range(self.world_size_y):
            for x in range(self.world_size_x):
                # FIXED: Correctly access the height map using [y, x]
                h = self.height_map[y, x]
                if h < self.water_level:
                    self.set_tile(x, y, Tile(terrain=TERRAIN_DATA["ocean"], is_water=True))
                elif h > self.ice_caps_level:
                    self.set_tile(x, y, Tile(terrain=TERRAIN_DATA["ice_cap"]))
                elif h > self.mountain_level:
                    self.set_tile(x, y, Tile(terrain=TERRAIN_DATA["mountain"]))
                else:
                    self.set_tile(x, y, Tile(terrain=TERRAIN_DATA["grassland"]))

        # Optional: Add rivers or other dynamic features after initial generation
        self.water_map = np.array(
            [[1 if self.get_tile(x, y).is_water else 0 for y in range(self.world_size_y)]
             for x in range(self.world_size_x)]
        )
        attempts = 0
        while attempts < 10 and self.carve_river_fast() == 0:
            attempts += 1

    def carve_rivers(self):
        """
        Generates a river from a random mountain/ice tile to the largest water cluster.
        This method is kept as is from your original code.
        """
        logger.debug("Generating river")

        # --- 1. Pick headwater from mountain tiles ---
        mountain_coords = [
            (x, y)
            for x in range(self.world_size_x)
            for y in range(self.world_size_y)
            if self.get_tile(x, y).terrain
            and self.get_tile(x, y).terrain.name in ["mountain", "ice_cap"]
        ]
        if not mountain_coords:
            return 0

        headwater = random.choice(mountain_coords)
        logger.info(f"Headwater at: {headwater}")

        # --- 2. Find largest water cluster or fallback to edge ---
        labeled_water, num_features = label(self.water_map)
        if num_features == 0:
            logger.info("No water clusters, sending river to edge.")
            edges = [
                lambda: (0, random.randint(0, self.world_size_y - 1)),
                lambda: (self.world_size_x - 1, random.randint(0, self.world_size_y - 1)),
                lambda: (random.randint(0, self.world_size_x - 1), 0),
                lambda: (random.randint(0, self.world_size_x - 1), self.world_size_y - 1),
            ]
            river_mouth = random.choice(edges)()
        else:
            sizes = [(labeled_water == i).sum() for i in range(1, num_features + 1)]
            largest_label = np.argmax(sizes) + 1
            candidates = np.argwhere(labeled_water == largest_label)
            if len(candidates) > 0:
                river_mouth = tuple(random.choice(candidates))
                river_mouth = (int(river_mouth[0]), int(river_mouth[1]))
            else:
                logger.info("No candidates for river mouth found.")
                return 0

        logger.info(f"River mouth at: {river_mouth}")

        # --- 3. BFS pathfinding (downhill/flat only) ---
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        visited = {headwater}
        parent = {}
        queue = deque([headwater])
        path = []

        while queue:
            x, y = queue.popleft()
            if (x, y) == river_mouth:
                cur = river_mouth
                while cur != headwater:
                    path.append(cur)
                    cur = parent[cur]
                path.append(headwater)
                path.reverse()
                break

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.world_size_x and 0 <= ny < self.world_size_y:
                    if (nx, ny) not in visited:
                        # FIXED: Correctly access the height map using [ny, nx]
                        if self.height_map[ny, nx] <= self.height_map[y, x]:
                            visited.add((nx, ny))
                            parent[(nx, ny)] = (x, y)
                            queue.append((nx, ny))

        if not path:
            logger.info("Failed to find river path.")
            return 0

        # --- 4. Carve river tiles ---
        logger.info("Carving river ...")
        for x, y in path:
            if not self.get_tile(x, y).is_water:
                self.set_tile(x, y, Tile(is_water=True, terrain=TERRAIN_DATA["river"]))
                self.water_map[x, y] = 1

        return len(path)

    def carve_river_fast(self, max_slope=0.05, lateral_chance=0.5, max_attempts=None):
        """
        Generates a realistic meandering river from a mountain/ice headwater to water or map edge.
        Optimized for large maps (up to 10k x 10k) using iterative gradient descent with random meanders.

        Parameters:
            max_slope (float): Maximum allowed slope per tile (0-1) to respect realism.
            lateral_chance (float): Chance to take a lateral step to induce meanders.
            max_attempts (int): Max steps to prevent infinite loops.

        Returns:
            int: Number of river tiles carved.
        """
        logger.debug("Generating river (fast)")
        max_attempts = max(self.world_size_x, self.world_size_y) / lateral_chance

        # --- 1. Pick headwater from mountain tiles ---
        mountain_coords = [
            (x, y)
            for x in range(self.world_size_x)
            for y in range(self.world_size_y)
            if self.get_tile(x, y).terrain
            and self.get_tile(x, y).terrain.name in ["mountain", "ice_cap"]
        ]
        if not mountain_coords:
            return 0

        headwater = random.choice(mountain_coords)
        logger.info(f"Headwater at: {headwater}")

        # --- 2. Determine river target ---
        labeled_water, num_features = label(self.water_map)
        if num_features == 0:
            # Fallback: random map edge
            edges = [
                lambda: (0, np.random.randint(self.world_size_y)),
                lambda: (self.world_size_x - 1, np.random.randint(self.world_size_y)),
                lambda: (np.random.randint(self.world_size_x), 0),
                lambda: (np.random.randint(self.world_size_x), self.world_size_y - 1),
            ]
            target = random.choice(edges)()
        else:
            sizes = [(labeled_water == i).sum() for i in range(1, num_features + 1)]
            largest_label = np.argmax(sizes) + 1
            candidates = np.argwhere(labeled_water == largest_label)
            target = tuple(candidates[np.random.randint(len(candidates))][::-1])  # (x, y)
        logger.info(f"River target at: {target}")

        # --- 3. Gradient descent with meanders ---
        river_path = [headwater]
        current = headwater
        attempts = 0

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                    (1, 1), (1, -1), (-1, 1), (-1, -1)]  # 8-way movement

        while current != target and attempts < max_attempts:
            x, y = current
            neighbors = []

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.world_size_x and 0 <= ny < self.world_size_y:
                    current_height = self.height_map[y, x]
                    neighbor_height = self.height_map[ny, nx]
                    slope = (current_height - neighbor_height) / max(1, np.hypot(dx, dy))
                    if slope >= 0 and slope <= max_slope:
                        neighbors.append((nx, ny, slope))

            if not neighbors:
                # If stuck, allow the least uphill neighbor within slope tolerance
                fallback = []
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.world_size_x and 0 <= ny < self.world_size_y:
                        current_height = self.height_map[y, x]
                        neighbor_height = self.height_map[ny, nx]
                        slope = (current_height - neighbor_height) / max(1, np.hypot(dx, dy))
                        if slope <= max_slope:  # small uphill allowed
                            fallback.append((nx, ny, slope))
                if fallback:
                    neighbors = fallback
                else:
                    break  # No valid moves, end river

            # Introduce randomness for meanders
            if np.random.rand() < lateral_chance:
                # Choose a lateral or less downhill neighbor
                neighbors.sort(key=lambda n: n[2])  # sort by slope ascending
                lateral_candidates = [n for n in neighbors if n[2] < max_slope / 2]
                if lateral_candidates:
                    next_tile = lateral_candidates[np.random.randint(len(lateral_candidates))]
                else:
                    next_tile = neighbors[np.random.randint(len(neighbors))]
            else:
                # Normally pick steepest downhill
                next_tile = max(neighbors, key=lambda n: n[2])

            current = (next_tile[0], next_tile[1])
            river_path.append(current)
            attempts += 1

            # Early exit if we reach existing water
            if self.get_tile(*current).is_water:
                break

        # --- 4. Carve river tiles ---
        logger.info(f"Carving river of length {len(river_path)}")
        for x, y in river_path:
            tile = self.get_tile(x, y)
            if not tile.is_water:
                self.set_tile(x, y, Tile(is_water=True, terrain=TERRAIN_DATA["river"]))
                self.water_map[y, x] = 1  # consistent indexing

        return len(river_path)

    def render(self, surface: pygame.Surface, camera: Camera):
        """
        Renders the visible portion of the world, making it efficient for a dynamic
        camera and world.
        """
        tile_size = camera.tile_size

        # Cull: compute visible bounds once
        start_x = max(int(camera.x // tile_size), 0)
        end_x   = min(int((camera.x + camera.width) // tile_size + 1), self.world_size_x)
        start_y = max(int(camera.y // tile_size), 0)
        end_y   = min(int((camera.y + camera.height) // tile_size + 1), self.world_size_y)

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
                        (87, 87, 87),
                        pygame.Rect(screen_x, screen_y, tile_size, tile_size),
                    )
