import random
import matplotlib.pyplot as plt
import numpy as np

import logging
logger = logging.getLogger(__name__)

WORLD_TILE_SIZE = 10
DEBUG_MAP = True

def load_resource_data(filename="resources_data.csv"):
    global resource_data
    resource_data = {}
    try:
        with open("resources_data.csv", "r") as f:
            lines = f.readlines()
            for line in lines[1:]:  # skip header
                parts = line.strip().split(",")
                if len(parts) >= 5:
                    name = parts[0]
                    r, g, b = int(parts[1]), int(parts[2]), int(parts[3])
                    abundance = float(parts[4])
                    resource_data[name] = Resource(name,(r,g,b),abundance)
    except Exception as e:
        logger.error(f"Error loading resource data: {e}")

class Terrain:
    def __init__(self, name, color=None, texture=None, resources=[]):
        self.name = name
        self.color = color
        self.texture = texture
        self.resources = resources



DEBUG_TOPO=True
def generate_gaussian_map(width, height, num_gaussians=5, seed=None):
    if seed is not None:
        np.random.seed(seed)

    # Grid coordinates
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    X, Y = np.meshgrid(x, y)

    Z = np.zeros_like(X)

    # Add multiple Gaussians
    for _ in range(num_gaussians):
        # Random center
        cx, cy = np.random.rand(), np.random.rand()
        # Random sigma (spread)
        sigma_x, sigma_y = np.random.uniform(0.05, 0.2), np.random.uniform(0.05, 0.2)
        # Random amplitude (+ can make mountains, - can make valleys)
        amplitude = np.random.uniform(-1, 1)

        gaussian = amplitude * np.exp(-(((X-cx)**2)/(2*sigma_x**2) + ((Y-cy)**2)/(2*sigma_y**2)))
        Z += gaussian

    # Normalize to [0, 1] for visualization
    Z = (Z - Z.min()) / (Z.max() - Z.min())

    if DEBUG_TOPO is True:
        plt.imshow(Z, cmap="terrain")
        plt.colorbar(label="Height")
        plt.title("Gaussian-based Topology Map")
        plt.savefig("topology_map.png")
    return Z


def generate_terrain_map(width, height, terrains, terrain_fractions=None, seed=None, num_gaussians=8):
    """
    Generate a terrain map from Gaussian height_map.
    terrains: dict of Terrain objects { "water": Terrain(...), ... }
    terrain_fractions: dict of target fractions per terrain, e.g.
        { "water": 0.3, "grass": 0.4, "forest": 0.2, "mountain": 0.1 }
        Values should sum to <=1. Remaining goes to last terrain.
    """
    if terrains is None or terrain_fractions is None:
        raise ValueError("Terrains and terrain_fractions must be provided")

    height_map = generate_gaussian_map(width, height, num_gaussians=num_gaussians, seed=seed)

    # Flatten map to compute percentiles
    h_flat = height_map.flatten()
    sorted_h = np.sort(h_flat)
    cumulative = 0
    thresholds = {}

    terrain_names = list(terrain_fractions.keys())
    fractions = list(terrain_fractions.values())

    for i, name in enumerate(terrain_names[:-1]):
        cumulative += fractions[i]
        idx = int(cumulative * len(sorted_h))
        thresholds[name] = sorted_h[idx]
    thresholds[terrain_names[-1]] = 1.0  # last terrain gets remaining heights

    # Build grid
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            h = height_map[y, x]
            # Pick terrain based on thresholds
            terrain_name = None
            for name in terrain_names:
                if h <= thresholds[name]:
                    terrain_name = name
                    break
            if terrain_name is None:
                terrain_name = terrain_names[-1]
            row.append(Tile(terrains[terrain_name]))
        grid.append(row)

    if DEBUG_MAP:
        # Convert to RGB numpy array
        img = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                img[y, x] = grid[y][x].terrain.color  # each Terrain has .color

        # Plot and save
        plt.figure(figsize=(6,6))
        plt.imshow(img)
        plt.axis("off")
        plt.savefig("terrain_map.png", bbox_inches="tight", pad_inches=0)
        plt.close()

    return grid


import random

import random

def place_resources(grid, abundance_percent=10):
    """
    Place resources on a percentage of eligible tiles.
    Even if a terrain supports resources, only some of its tiles will actually get them.
    """
    abundance_percent = max(0, min(100, abundance_percent))  # clamp 0–100

    height = len(grid)
    width = len(grid[0])
    logger.debug(f"Placing resources on map of size {width}x{height} with abundance {abundance_percent}%")

    for y in range(height):
        for x in range(width):
            tile = grid[y][x]
            # Only terrains with resources are considered
            if tile.resource is None and len(tile.terrain.resources) > 0:
                # Roll a dice for this tile
                resource = random.choice(tile.terrain.resources)
                if random.random() < (abundance_percent*resource.abundance / 100.0):
                    tile.resource = resource

    return grid

if __name__ == "__main__":
    # Example terrains and resources
    load_resource_data(filename="resources_data.csv")

    marker_map = {
        "stone": "^",   # triangle
        "food": "o",    # circle
        "fish": "o",    # circle
        "wood": "s"     # square
    }

    terrains = {
        "water": Terrain("water", color=(0,0,255), resources=[resource_data['']]),
        "grass": Terrain("grass", color=(0,255,0), resources=[wood]),
        "forest": Terrain("forest", color=(34,139,34), resources=[wood, food]),
        "mountain": Terrain("mountain", color=(139,137,137), resources=[stone, coal, iron]),
        "barren": Terrain("barren", color=(200,150,97), resources=[stone])
    }

    fractions = {
        "water": 0.2,
        "grass": 0.4,
        "forest": 0.2,
        "barren": 0.05,
        "mountain": 0.15,
    }

    # Generate terrain
    WIDTH, HEIGHT = 500, 500
    map_grid = generate_terrain_map(WIDTH, HEIGHT, terrains=terrains, terrain_fractions=fractions, seed=None, num_gaussians=100)
    map_grid = place_resources(map_grid, abundance_percent=0.1)

    # Convert to RGB numpy array
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    resource_x, resource_y, resource_colors, resource_markers = [], [], [], []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            img[y, x] = map_grid[y][x].terrain.color  # each Terrain has .color
            if map_grid[y][x].resource is not None:
                resource_x.append(x)
                resource_y.append(y)
                resource_colors.append(np.array(map_grid[y][x].resource.color) / 255.0)
                resource_markers.append(marker_map.get(map_grid[y][x].resource.name, "x"))

    # Plot and save
    plt.figure(figsize=(6,6))
    plt.imshow(img)
    # Scatter each resource with its marker
    for x, y, c, m in zip(resource_x, resource_y, resource_colors, resource_markers):
        plt.scatter(x, y, c=[c], marker=m, s=10, linewidths=0.8)

    plt.axis("off")
    plt.savefig("terrain_map.png", bbox_inches="tight", pad_inches=0)
    plt.close()
    print("Saved map as terrain_map.png")