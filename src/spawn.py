from .character import *
from .map_data import *

def find_spawn_point(character, grid, min_neighbors=4):
    """
    Find a spawn point for the given character on the map.

    character: Character object (used for blocked_terrains)
    grid: 2D list of Tile objects
    min_neighbors: minimum number of allowed neighbors around spawn tile
    Returns: (px, py) pixel coordinates
    """
    height = len(grid)
    width = len(grid[0])
    candidates = []

    for y in range(height):
        for x in range(width):
            tile = grid[y][x]
            # Tile must be allowed for this character and have no resource
            if tile.terrain.name in character.blocked_terrains or tile.resource is not None:
                continue

            # Count valid neighbors
            valid_neighbors = 0
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    n_tile = grid[ny][nx]
                    if n_tile.terrain.name not in character.blocked_terrains and n_tile.resource is None:
                        valid_neighbors += 1

            if valid_neighbors >= min_neighbors:
                candidates.append((x, y))

    if not candidates:
        raise ValueError("No suitable spawn point found")

    gx, gy = random.choice(candidates)
    px = gx * WORLD_TILE_SIZE + WORLD_TILE_SIZE / 2
    py = gy * WORLD_TILE_SIZE + WORLD_TILE_SIZE / 2
    return px, py