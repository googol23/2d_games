import pygame
from . import *

# --- Render function ---
def render_map(surface, map_grid, characters, camera_x, camera_y,
               window_width, window_height, min_tile_size=1, max_tile_size=64):
    map_width = len(map_grid[0])
    map_height = len(map_grid)

    # Determine tile size
    tile_size = min(window_width // map_width, window_height // map_height)
    if tile_size < min_tile_size:
        scale_x = window_width / map_width
        scale_y = window_height / map_height
        tile_size = int(max(min_tile_size, min(scale_x, scale_y)))
    tile_size = min(tile_size, max_tile_size)

    # Visible tiles
    tiles_x = window_width // tile_size + 2
    tiles_y = window_height // tile_size + 2
    start_tile_x = int(camera_x // tile_size)
    start_tile_y = int(camera_y // tile_size)
    offset_x = -(camera_x % tile_size)
    offset_y = -(camera_y % tile_size)

    surface.fill((0,0,0))

    # Draw tiles and resources
    for y in range(tiles_y):
        for x in range(tiles_x):
            mx = start_tile_x + x
            my = start_tile_y + y
            if mx >= map_width or my >= map_height:
                continue
            tile = map_grid[my][mx]
            pygame.draw.rect(surface, tile.terrain.color,
                             pygame.Rect(x*tile_size+offset_x, y*tile_size+offset_y, tile_size, tile_size))
            if tile.resource:
                pygame.draw.circle(surface, tile.resource.color,
                                   (int(x*tile_size+offset_x + tile_size/2),
                                    int(y*tile_size+offset_y + tile_size/2)),
                                   max(2, tile_size//4))

    # Draw characters
    for c in characters:
        screen_x = (c.x - start_tile_x)*tile_size + offset_x
        screen_y = (c.y - start_tile_y)*tile_size + offset_y
        pygame.draw.rect(surface, (255,0,0),
                         pygame.Rect(int(screen_x - tile_size/2),
                                     int(screen_y - tile_size/2),
                                     tile_size, tile_size))
    return tile_size
