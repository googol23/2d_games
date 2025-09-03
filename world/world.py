import terrain.terrain as terrain
import resources
import world.topology as topology

import random
import pygame
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from collections import deque
from scipy.ndimage import distance_transform_edt

from scipy.ndimage import label, binary_dilation
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

import logging
logger = logging.getLogger(__name__)

class Tile:
    """Represents a single world tile"""
    def __init__(self, terrain):
        self.terrain = terrain

class World:
    def __init__(self, world_size=None, tiles=None, characters=None):
        self.world_size = world_size
        self.tiles = tiles or []
        self.characters = characters or []


    def find_lakes_and_ponds(self, lake_threshold=0.01):
        """
        Detect all water clusters completely surrounded by land and
        rename them to "water_pond" or "water_lake" depending on size.

        lake_threshold: fraction of total map area above which a cluster is a lake
        """
        logger.debug("Finding and classifying water bodies...")
        total_tiles = self.world_size * self.world_size

        # Label connected water clusters
        labeled_water, num_features = label(self.water_map)

        for i in range(1, num_features+1):
            coords = np.argwhere(labeled_water == i)

            # Skip clusters touching map edge
            if np.any(coords[:,0] == 0) or np.any(coords[:,0] == self.world_size-1) \
            or np.any(coords[:,1] == 0) or np.any(coords[:,1] == self.world_size-1):
                continue

            cluster_size = len(coords)
            # Decide terrain type based on relative size
            terrain_type = "water_lake" if (cluster_size / total_tiles) >= lake_threshold else "water_pond"

            # Assign new terrain type
            for y, x in coords:
                self.tiles[y][x] = Tile(terrain_type)


    def generate_river(self):
        """
        Generate a river from a random mountain tile to the largest water cluster
        using A* pathfinding over the height map. The river prefers downhill flow.
        """
        logger.debug("Generating river")
        # --- 1. Identify mountain tiles ---
        mountain_coords = [(y, x) for y in range(self.world_size)
                                for x in range(self.world_size)
                                if self.tiles[y][x].terrain == "mountain"]
        if not mountain_coords:
            print("No mountains to start a river.")
            return
        start = random.choice(mountain_coords)

        # --- 2. Identify largest water cluster ---
        water_map = np.array([[int("water" in self.tiles[y][x].terrain)
                            for x in range(self.world_size)]
                            for y in range(self.world_size)])
        labeled_water, num_features = label(water_map)
        if num_features == 0:
            print("No water to flow into.")
            return
        sizes = [(labeled_water==i).sum() for i in range(1, num_features+1)]
        largest_cluster_label = np.argmax(sizes) + 1
        water_coords = np.argwhere(labeled_water==largest_cluster_label)

        # Pick a random tile in the largest water cluster as the target
        end = tuple(random.choice(water_coords))

        # --- 3. Prepare height-based cost matrix ---
        # Lower tiles = lower cost; uphill = penalized
        cost_matrix = np.ones((self.world_size, self.world_size))

        # Add small random noise to the cost matrix
        noise = np.random.rand(self.world_size, self.world_size) * 9.5  # tweak factor
        cost_matrix += noise

        for y in range(self.world_size):
            for x in range(self.world_size):
                # Penalize tiles higher than current start to prefer downhill
                cost_matrix[y, x] += max(0, self.height_map[y, x] - self.height_map[start[0], start[1]])

        # --- 4. Use pathfinding library ---
        grid = Grid(matrix=cost_matrix.tolist())
        start_node = grid.node(start[1], start[0])  # note: Grid uses (x,y)
        end_node = grid.node(end[1], end[0])

        finder = AStarFinder(diagonal_movement=True)  # allow diagonal river flow
        path, _ = finder.find_path(start_node, end_node, grid)

        if not path:
            print("Failed to find river path.")
            return

        # --- 5. Carve river into map ---
        for x, y in path:  # path returned as (x,y)
            if "water" not in self.tiles[y][x].terrain:
                self.tiles[y][x] = Tile("water_river")
                self.water_map[y][x] = 1


    def smooth_terrains(self, target, final_state, friendly, flip_edge_touching=False):
        """
        Convert entire 'target' patches to 'final_state' if every external neighbor
        around the patch belongs to 'friendly'.
        """
        target_map = np.array([
            [1 if (tile := self.tiles[y][x]) is not None and tile.terrain == target else 0
            for x in range(self.world_size)]
            for y in range(self.world_size)
        ])
        if target_map.sum() == 0:
            return 0

        structure = np.ones((3, 3), dtype=int)
        labeled, num_features = label(target_map, structure=structure)
        converted_patches = 0

        all_friendly = set(friendly)
        # Automatically treat any terrain containing "water" as friendly
        for y in range(self.world_size):
            for x in range(self.world_size):
                tile = self.tiles[y][x]
                if tile and "water" in tile.terrain:
                    all_friendly.add(tile.terrain)

        for comp in range(1, num_features + 1):
            patch_mask = (labeled == comp)

            # Dilate to get external border
            border_mask = binary_dilation(patch_mask, structure=np.ones((3, 3))) & (~patch_mask)

            # Check if touches edge
            touches_edge = np.any(border_mask[0,:]) or np.any(border_mask[-1,:]) or \
                        np.any(border_mask[:,0]) or np.any(border_mask[:,-1])
            if touches_edge and not flip_edge_touching:
                continue

            border_coords = np.argwhere(border_mask)
            # If all border tiles are friendly, flip patch
            if all(self.tiles[y][x] is not None and self.tiles[y][x].terrain in all_friendly
                for y, x in border_coords):
                for y, x in np.argwhere(patch_mask):
                    self.tiles[y][x] = Tile(final_state)
                converted_patches += 1


    def generate(self, terrain_weights, water_level=0.3, mountain_level=0.7, n_of_peaks=5, seed=None):
        """
        world_size: world size
        terrain_weights: dict {terrain_name: weight} for random terrain distribution
        water_level: normalized height below which tiles are water
        mountain_level: normalized height above which tiles are mountains
        """
        logger.info("(...) Now the earth was formless and empty, darkness was over the surface of the deep (...)")
        if len(terrain.TERRAIN_DATA) == 0:
            terrain.load_terrains_data("terrains_data.json")

        if len(resources.RESOURCE_DATA) == 0:
            resources.load_resource_data("resource_data.json")

        self.tiles = [[None for _ in range(self.world_size)] for _ in range(self.world_size)]

        # Generate height map
        self.height_map = topology.generate_topological_map(self.world_size, self.world_size, n_of_peaks=n_of_peaks, seed=seed, debug_name="height_map")

        # Create a binary map: 1 for water, 0 otherwise
        self.water_map = np.zeros(shape=(self.world_size,self.world_size))

        # First assign water/mountain strictly based on height
        for y in range(self.world_size):
            for x in range(self.world_size):
                h = self.height_map[y, x]
                if h < water_level:
                    self.tiles[y][x] = Tile("water")
                    self.water_map[y, x] = 1
                elif h > mountain_level:
                    self.tiles[y][x] = Tile("mountain")
                if h > 0.95:
                    self.tiles[y][x] = Tile("ice_cap")

       # Available terrains (exclude water/mountain)
        available_terrains = [name for name in terrain_weights if name not in ["water", "mountain"]]

        # Count remaining empty tiles
        empty_tiles = sum(1 for row in self.tiles for t in row if t is None)

        # Compute target count per terrain based on weights
        weights = np.array([terrain_weights[name] for name in available_terrains], dtype=float)
        weights /= weights.sum()
        target_counts = {name: int(round(w * empty_tiles)) for name, w in zip(available_terrains, weights)}

        # Fix rounding errors
        remaining = empty_tiles - sum(target_counts.values())
        for name in available_terrains:
            if remaining <= 0:
                break
            target_counts[name] += 1
            remaining -= 1

        # Generate Gaussian-smoothed noise maps for clustering
        terrain_noise = {name: gaussian_filter(np.random.rand(self.world_size, self.world_size), sigma=2)
                        for name in available_terrains}

        # Get list of empty coordinates and shuffle to avoid directional artifacts
        empty_coords = [(y, x) for y in range(self.world_size) for x in range(self.world_size) if self.tiles[y][x] is None]
        random.shuffle(empty_coords)

        # Assign terrains based on max noise among valid terrains
        for y, x in empty_coords:
            valid_terrains = [name for name in available_terrains if target_counts[name] > 0]
            if not valid_terrains:
                break  # all tiles assigned
            values = [terrain_noise[name][y, x] for name in valid_terrains]
            chosen = valid_terrains[np.argmax(values)]

            self.tiles[y][x] = Tile(chosen)
            target_counts[chosen] -= 1

        # Generate water bodies
        self.find_lakes_and_ponds()
        self.generate_river()

        distance_to_water_map = distance_transform_edt(1 - self.water_map)  # distance to nearest water
        self.fertility_map = 1 - (distance_to_water_map / distance_to_water_map.max())


        plt.figure(figsize=(6,6))
        plt.imshow(self.fertility_map, cmap="RdYlGn")
        plt.axis('off')                          # remove axes
        plt.gca().set_position([0, 0, 1, 1])
        plt.contour(self.height_map, levels=10, colors='blue', linewidths=1, origin='lower')
        plt.savefig("fertility_map.png")
        plt.close()

        self.smooth_terrains(target="barren", final_state="grassland", friendly={"forest", "grassland", *[n for n in terrain.TERRAIN_DATA.keys() if "water" in n]}, flip_edge_touching=False)
        self.smooth_terrains(target="forest", final_state="barren", friendly={"barren"}, flip_edge_touching=False)
        # self.smooth_terrains(target="grassland", final_state="forest", friendly={"forest"}, flip_edge_touching=False)



    def add_character(self, character):
        self.characters.append(character)

    # ------------------------------
    # Render Method
    # ------------------------------
    def render_world(self, screen):
        screen_width, screen_height = screen.get_size()
        tile_width = screen_width / self.world_size
        tile_height = screen_height / self.world_size

        # Draw tiles
        for y in range(self.world_size):
            for x in range(self.world_size):
                rect = pygame.Rect(x*tile_width, y*tile_height, tile_width, tile_height)
                try:
                    pygame.draw.rect(screen, terrain.TERRAIN_DATA[self.tiles[y][x].terrain].color, rect)
                except Exception as e:
                    logger.warning(f"Missing terrain data for {self.tiles[y][x].terrain}\n{e}")

    # ------------------------------
    # Simple Draw Method
    # ------------------------------
    def draw_world(self):
        img = np.zeros((self.world_size, self.world_size, 3), dtype=np.uint8)

        for y in range(self.world_size):
            for x in range(self.world_size):
                tile = self.tiles[y][x]
                if tile is not None:
                    try:
                        color = terrain.TERRAIN_DATA[tile.terrain].color
                        if tile and color:
                            img[y, x] = color
                    except Exception as e:
                        print(f"Error at tile ({x}, {y}): {e}, {tile.terrain}")

        plt.figure(figsize=(8, 8))
        plt.imshow(img)
        plt.gca().set_position([0, 0, 1, 1])
        plt.contour(self.height_map, levels=10, colors='blue', linewidths=1, origin='lower')
        plt.axis('off')
        plt.title("World Map")
        plt.savefig("world_map.png")
        plt.close()


if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Ensure terrain data is loaded
    terrain.load_terrains_data("terrains_data.json")

    world = World(100)
    world.generate(
        terrain_weights={
            "water": 1,
            "barren": .5,
            "grassland": 1,
            "forest": 1,
            "mountain": 1},
        water_level=0.1,
        mountain_level=0.7,
        n_of_peaks=100,
        # seed=23
        )
    world.draw_world()