import pygame
import numpy as np
SHOW_GRID = False

def draw_grid(grid_width, grid_height, tile_width, tile_height,
              offset_x=0, color=(0, 255, 0, 80),
              grid_to_iso=None) -> pygame.Surface:
    """
    Returns a pre-rendered grid surface.
    grid_to_iso must be passed in from the main program.
    """
    if grid_to_iso is None:
        raise ValueError("draw_grid requires a grid_to_iso function.")

    world_width = np.hypot(grid_width, grid_height) * tile_width
    world_height = world_width

    grid_surface = pygame.Surface((world_width, world_height), pygame.SRCALPHA)

    # Horizontal grid lines
    for row in range(grid_height + 1):
        start = grid_to_iso(0, row)
        end = grid_to_iso(grid_width, row)
        pygame.draw.line(grid_surface, color,
                         (start[0] + offset_x, start[1]),
                         (end[0] + offset_x, end[1]), width=4)

    # Vertical grid lines
    for col in range(grid_width + 1):
        start = grid_to_iso(col, 0)
        end = grid_to_iso(col, grid_height)
        pygame.draw.line(grid_surface, color,
                         (start[0] + offset_x, start[1]),
                         (end[0] + offset_x, end[1]), width=4)

    return grid_surface
