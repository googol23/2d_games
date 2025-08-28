import random
from noise import pnoise2

class Resource:
    def __init__(self, name, color=None, texture=None):
        self.name = name
        self.color = color
        self.texture = texture  # could be a Pygame surface

class Terrain:
    def __init__(self, name, color=None, texture=None, possible_resources=None):
        self.name = name
        self.color = color
        self.texture = texture
        self.possible_resources = possible_resources or []

class Tile:
    """Represents a single map tile"""
    def __init__(self, terrain, resource=None):
        self.terrain = terrain
        self.resource = resource

def generate_terrain_map(width, height, scale=0.1, seed=None, terrains=None):
    """Generate a terrain map using Perlin noise"""
    if seed is not None:
        random.seed(seed)
    if terrains is None:
        raise ValueError("Terrains must be provided")

    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            h = pnoise2(x*scale, y*scale, repeatx=1024, repeaty=1024)
            # Simple height thresholds
            if h < -0.05:
                terrain = terrains["water"]
            elif h < 0.3:
                terrain = terrains["grass"]
            else:
                terrain = terrains["mountain"]
            row.append(Tile(terrain))
        grid.append(row)
    return grid

def place_resources(grid, num_resources=50):
    """Place resources according to terrain's possible_resources"""
    height = len(grid)
    width = len(grid[0])
    for _ in range(num_resources):
        attempts = 0
        while attempts < 100:
            x = random.randint(0, width-1)
            y = random.randint(0, height-1)
            tile = grid[y][x]
            if tile.resource is None and tile.terrain.possible_resources:
                tile.resource = random.choice(tile.terrain.possible_resources)
                break
            attempts += 1
    return grid
