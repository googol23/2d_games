import numpy as np
import random
from collections import deque
from scipy.ndimage import label
from functools import cached_property
from pydantic.dataclasses import dataclass
from pathlib import Path
import json

from terrain import TERRAIN_DATA, load_terrains_data
from tree import Tree, TREE_DATA, load_trees

from .tile import Tile
from .topology import generate_topological_map, visualize_topological_map

import logging
logger = logging.getLogger(__name__)

@dataclass
class WorldGenConfig:
    SIZE_X: int = 50   # tiles
    SIZE_Y: int = 50   # tiles
    SCALE: float = 10  # meters
    TILE_SUBDIVISIONS: int = 10  # subdivisions per tile
    WATER_RATIO:float = 0.1
    MOUNTAIN_RATIO:float = 0.15
    ICE_CAP_RATIO:float = 0.01

    def __str__(self) -> str:
        return (
            f"WorldGenConfig("
            f"SIZE_X={self.SIZE_X}, "
            f"SIZE_Y={self.SIZE_Y}, "
            f"SCALE={self.SCALE}, "
            f"TILE_SUBDIVISIONS={self.TILE_SUBDIVISIONS})"
        )

    @classmethod
    def from_file(cls, path: str | Path | None = None):
        """Load configuration from a JSON file with Pydantic validation."""
        if path is None:
            return
        path = Path(path)
        with path.open("r") as f:
            data = json.load(f)
        return cls(**data)  # Pydantic validates here


class WorldGen:
    """
    Game world generator.
    """

    def __init__(self, config:WorldGenConfig | None = None):
        self.config:WorldGenConfig = WorldGenConfig() if config is None else config


        logger.info("Generating world ...")
        self.tiles: np.ndarray[Tile] = np.empty((self.size_y, self.size_x), dtype=object)
        self.elements: np.ndarray = np.empty((self.topo_size_y, self.topo_size_x), dtype=object)
        self.topology: np.ndarray[np.float16] = np.zeros((self.topo_size_y, self.topo_size_x), dtype=np.float16)
        self.obstacle: np.ndarray[np.bool_] = np.zeros((self.topo_size_y, self.topo_size_x), dtype=np.bool_)

    def reset(self):
        # --- clear previous generation ---
        self.tiles[:, :] = None                  # clears all Tile references
        self.elements[:, :] = None               # clears all Trees / objects
        self.topology[:, :] = 0                  # reset heights
        self.obstacle[:, :] = 0                  # reset obstacles

    @property
    def size_x(self)->int:
        return self.config.SIZE_X

    @property
    def size_y(self)->int:
        return self.config.SIZE_Y

    @property
    def topo_size_x(self)->int:
        return self.config.SIZE_X * self.config.TILE_SUBDIVISIONS

    @property
    def topo_size_y(self)->int:
        return self.config.SIZE_Y * self.config.TILE_SUBDIVISIONS

    @property
    def scale(self)->float:
        return self.config.SCALE

    @cached_property
    def tile_heights_map(self) -> np.ndarray:
        """
        Returns the average height per tile, cached until topology or config changes.
        """
        N = self.config.TILE_SUBDIVISIONS
        reshaped = self.topology.reshape(self.size_y, N, self.size_x, N)
        return reshaped.mean(axis=(1, 3))

    def get_tile(self, x: int, y: int) -> Tile:
        """Retrieves a tile at the given coordinates."""
        return self.tiles[y,x]

    def set_tile(self, x: int, y: int, tile: Tile):
        """Sets a tile at the given coordinates."""
        self.tiles[y,x] = tile

    def __str__(self):
        return self.config.__str__()


    def generate(self):
        """
        Generates the height map and assigns terrains based on height.

        """
        self.reset()
        # 0. Loading neccesary data
        if len(TREE_DATA) == 0:
            load_trees()

        if len(TERRAIN_DATA) == 0:
            load_terrains_data()

        logger.info(f"Terrain models:{len(TERRAIN_DATA)}")
        logger.info(f"Tree models:{len(TREE_DATA)}")

        logger.info(" ... pre-allocating world tiles")
        # 1. populate world with Tiles
        for y in range(self.size_y):
            for x in range(self.size_x):
                self.tiles[y, x] = Tile()

        # 2. build topological map
        self.topology = generate_topological_map(
            self.topo_size_x, self.topo_size_y, n_of_peaks=random.randint(5, 10)
        )
        visualize_topological_map(self.topology)
        # invalidate cached tile_height_map
        if "tile_heights_map" in self.__dict__:
            del self.__dict__["tile_heights_map"]

        # 3. Compute thresholds from height distribution
        flat_heights = self.tile_heights_map.flatten()
        water_level = np.percentile(flat_heights, self.config.WATER_RATIO * 100)
        mountain_level = np.percentile(flat_heights, (1 - self.config.MOUNTAIN_RATIO) * 100)
        ice_caps_level = np.percentile(flat_heights, (1 - self.config.ICE_CAP_RATIO) * 100)

        logger.info("Filling world with terrains based on height map")
        # 4. Compute Tile terrain tipe based on average Tile height
        for y in range(self.size_y):
            for x in range(self.size_x):
                h = self.tile_heights_map[y, x]
                if h < water_level:
                    self.set_tile(x, y, Tile(terrain=TERRAIN_DATA["ocean"], is_water=True))
                elif h > ice_caps_level:
                    self.set_tile(x, y, Tile(terrain=TERRAIN_DATA["ice_cap"]))
                elif h > mountain_level:
                    self.set_tile(x, y, Tile(terrain=TERRAIN_DATA["mountain"]))
                else:
                    self.set_tile(x, y, Tile(terrain=TERRAIN_DATA["grassland"]))

        # 5. Calsify water bodies
        self.water_map = np.array(
            [[1 if self.get_tile(x, y).is_water else 0 for x in range(self.size_x)]
            for y in range(self.size_y)],
            dtype=np.int8
        )
        self.classify_water_bodies()

        # 6. Add rivers
        attempts = 0
        while attempts < 10 and self.carve_river_fast() == 0:
            attempts += 1

        self.generate_forest_patches()
        self.populate_trees()

        return self.tiles, self.elements, self.topology, self.obstacle

    def carve_rivers(self):
        """
        Generates a river from a random mountain/ice tile to the largest water cluster.
        This method is kept as is from your original code.
        """
        logger.debug("Generating river")

        # --- 1. Pick headwater from mountain tiles ---
        mountain_coords = [
            (x, y)
            for x in range(self.size_x)
            for y in range(self.size_y)
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
                lambda: (0, random.randint(0, self.size_y - 1)),
                lambda: (self.size_x - 1, random.randint(0, self.size_y - 1)),
                lambda: (random.randint(0, self.size_x - 1), 0),
                lambda: (random.randint(0, self.size_x - 1), self.size_y - 1),
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
                if 0 <= nx < self.size_x and 0 <= ny < self.size_y:
                    if (nx, ny) not in visited:
                        # FIXED: Correctly access the height map using [ny, nx]
                        if self.topology[ny, nx] <= self.topology[y, x]:
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
                self.water_map[y, x] = 1

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
        max_attempts = max(self.size_x, self.size_y) / lateral_chance

        # --- 1. Pick headwater from mountain tiles ---
        mountain_coords = [
            (x, y)
            for x in range(self.size_x)
            for y in range(self.size_y)
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
                lambda: (0, np.random.randint(self.size_y)),
                lambda: (self.size_x - 1, np.random.randint(self.size_y)),
                lambda: (np.random.randint(self.size_x), 0),
                lambda: (np.random.randint(self.size_x), self.size_y - 1),
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
                    # (1, 1), (1, -1), (-1, 1), (-1, -1)
                    ]  # 8-way movement

        while current != target and attempts < max_attempts:
            x, y = current
            neighbors = []

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size_x and 0 <= ny < self.size_y:
                    current_height = self.topology[y, x]
                    neighbor_height = self.topology[ny, nx]
                    slope = (current_height - neighbor_height) / max(1, np.hypot(dx, dy))
                    if slope >= 0 and slope <= max_slope:
                        neighbors.append((nx, ny, slope))

            if not neighbors:
                # If stuck, allow the least uphill neighbor within slope tolerance
                fallback = []
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.size_x and 0 <= ny < self.size_y:
                        current_height = self.topology[y, x]
                        neighbor_height = self.topology[ny, nx]
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

    def classify_water_bodies(self):
        """
        Reclassify water tiles into pond/lake/ocean.
        Oceans are water bodies that touch the map edge.
        Lakes and ponds must be surrounded by land.
        """
        logger.info("Classifying water bodies...")

        # Label connected water regions
        labeled, num_features = label(self.water_map)
        if num_features == 0:
            logger.info("No water bodies found.")
            return


        # Thresholds relative to map size
        total_tiles = self.size_x * self.size_y
        pond_thresh = 0.005 * total_tiles
        lake_thresh = 0.010 * total_tiles

        for label_id in range(1, num_features + 1):
            coords = np.argwhere(labeled == label_id)
            size = len(coords)

            # Check if touches map edge → Ocean
            touches_edge = any(
                x == 0 or y == 0 or x == self.size_x - 1 or y == self.size_y - 1
                for y, x in coords
            )

            if touches_edge:
                new_terrain = TERRAIN_DATA["ocean"]
            elif size < pond_thresh:
                new_terrain = TERRAIN_DATA["pond"]
            elif size < lake_thresh:
                new_terrain = TERRAIN_DATA["lake"]
            else:
                # Large but enclosed → still lake
                new_terrain = TERRAIN_DATA["lake"]

            for y, x in coords:  # careful: (row, col) → (y, x)
                self.get_tile(x, y).terrain = new_terrain

    def generate_forest_patches(self, n_patches=5, percent_of_grassland=0.05, spread_chance=0.6):
        """
        Converts grassland tiles into forest patches.

        Parameters:
            n_patches (int): Number of forest patches to create.
            percent_of_grassland (float): Fraction of total grassland tiles to convert per patch (0-1).
            spread_chance (float): Probability of forest spreading to a neighboring grassland tile.
        """
        logger.info("Generating forest patches...")

        # Find all grassland tiles
        grassland_coords = [
            (x, y) for y in range(self.size_y) for x in range(self.size_x)
            if self.get_tile(x, y).terrain.name == "grassland"
        ]
        total_grassland = len(grassland_coords)
        if total_grassland == 0:
            return

        for _ in range(n_patches):
            if not grassland_coords:
                break

            # Pick a random seed for this patch
            seed = random.choice(grassland_coords)

            # Calculate max tiles for this patch as a percentage of remaining grassland
            max_patch_size = max(1, int(total_grassland * percent_of_grassland))

            patch_tiles = set([seed])
            frontier = [seed]

            while frontier and len(patch_tiles) < max_patch_size:
                x, y = frontier.pop()
                # Neighboring positions (4-way)
                neighbors = [
                    (nx, ny) for nx, ny in
                    [(x+1,y), (x-1,y), (x,y+1), (x,y-1)]
                    if 0 <= nx < self.size_x and 0 <= ny < self.size_y
                ]
                for nx, ny in neighbors:
                    tile = self.get_tile(nx, ny)
                    if tile.terrain.name == "grassland" and (nx, ny) not in patch_tiles:
                        if random.random() < spread_chance:
                            patch_tiles.add((nx, ny))
                            frontier.append((nx, ny))

            # Apply forest terrain
            for x, y in patch_tiles:
                self.get_tile(x, y).terrain = TERRAIN_DATA["forest"]
                grassland_coords.remove((x, y))

            # Update remaining grassland count
            total_grassland = len(grassland_coords)


    def populate_trees(self):
        """
        Places Tree objects on the map according to terrain type and density.
        """

        logger.info("Populating trees...")

        for (y, x), _ in np.ndenumerate(self.elements):
            world_x = x / self.config.TILE_SUBDIVISIONS
            world_y = y / self.config.TILE_SUBDIVISIONS

            assert 0 <= world_x < self.size_x
            assert 0 <= world_y < self.size_y

            tile = self.get_tile(int(world_x), int(world_y))

            # Determine density based on terrain
            if tile.terrain.name == "forest":
                density = 0.99
            elif tile.terrain.name == "grassland":
                density = 0.00
            else:
                continue  # Skip non-plantable terrains

            if random.random() > density:
                continue  # Skip based on density


            # Randomly pick cells for trees
            if self.elements[y,x] is None:
                tree_model = random.choice(tile.terrain.vegetation.trees)
                t = Tree(model=TREE_DATA[tree_model])
                t.set_coordinates(world_x, world_y)
                self.elements[y,x] = t
