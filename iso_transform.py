from world import World, WorldGen, WorldGenConfig
from camera import CameraIso, CameraIsoConfig
import pygame, random, os
from pathlib import Path
import glob
import numpy as np

# --- Logging setup ---
import logging
logger = logging.getLogger("main")
PROJECT_PREFIXES = ("main","world", "terrain", "pgi", "manager", "tree")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
for name, log_obj in logging.root.manager.loggerDict.items():
    if isinstance(log_obj, logging.Logger) and name.startswith(PROJECT_PREFIXES):
        log_obj.addHandler(ch)
        log_obj.setLevel(logging.DEBUG)

# World configuration
# --- Initialize world ---
world_config = WorldGenConfig(  WIDTH = 80,
                                HEIGHT= 80,
                                SCALE = 10,
                                TILE_SUBDIVISIONS=2,
                                WATER_RATIO=0.15,
                                MOUNTAIN_RATIO=0.15,
                                ICE_CAP_RATIO=0.01
                              )
world_gentor = WorldGen(config=world_config)
my_world = World(world_gentor)

# Camera configuration
cam_config = CameraIsoConfig(
        fps = 120,
        speed_tiles = 20,
        screen_with = 1600,
        screen_height = 900,
        tile_width = 128,
        tile_height = 64
    )
camera = CameraIso(my_world, 0, 0, config=cam_config)

# --- Transformation matrices ---

w2s_matrix = np.array([
    [cam_config.TILE_WIDTH / 2, cam_config.TILE_HEIGHT / 2],
    [-cam_config.TILE_WIDTH / 2, cam_config.TILE_HEIGHT / 2]
])

s2w_matrix = np.linalg.inv(w2s_matrix)

screen_offset = np.array([cam_config.SCREEN_WIDTH / 2, cam_config.SCREEN_HEIGHT / 4])

def world_to_screen(x, y):
    """
    Transforms world coordinates (x, y) to screen coordinates.
    x and y can be scalars or NumPy arrays.
    """
    world_coords = np.stack([x, y], axis=-1)
    screen_coords = world_coords @ w2s_matrix + screen_offset
    return screen_coords.astype(int)

def screen_to_world(screen_x, screen_y):
    """
    Transforms screen coordinates (screen_x, screen_y) to world coordinates.
    screen_x and screen_y can be scalars or NumPy arrays.
    """
    screen_coords = np.stack([screen_x, screen_y], axis=-1)
    world_coords = (screen_coords - screen_offset) @ s2w_matrix
    return world_coords.astype(int)

def get_tiles_in_rect(selection_rect, camera_x, camera_y, world_config, cam_config):
    """
    Calculates the set of world grid tiles that intersect with a given screen rectangle.

    This is an optimized function that first converts the screen rectangle's corners
    to world coordinates to define a smaller search area, rather than iterating over
    the entire world grid.

    Args:
        selection_rect (pygame.Rect): The rectangle on the screen.
        camera_x (int): The camera's X offset in pixels.
        camera_y (int): The camera's Y offset in pixels.
        world_config (WorldGenConfig): The world configuration object.
        cam_config (CameraIsoConfig): The camera configuration object.

    Returns:
        set[tuple[int, int]]: A set of (x, y) world coordinates for the intersecting tiles.
    """
    # 1. Convert screen rect corners to world coordinates to define a search area.
    rect_corners_screen_x = np.array([selection_rect.left, selection_rect.right, selection_rect.right, selection_rect.left]) - camera_x
    rect_corners_screen_y = np.array([selection_rect.top, selection_rect.top, selection_rect.bottom, selection_rect.bottom]) - camera_y
    world_corners = screen_to_world(rect_corners_screen_x, rect_corners_screen_y)

    # 2. Determine the bounding box of the search area in the world grid.
    min_wx = max(0, int(np.min(world_corners[:, 0])) - 2)
    max_wx = min(world_config.WIDTH, int(np.max(world_corners[:, 0])) + 2)
    min_wy = max(0, int(np.min(world_corners[:, 1])) - 2)
    max_wy = min(world_config.HEIGHT, int(np.max(world_corners[:, 1])) + 2)

    # 3. Iterate only over tiles in the bounding box and check for intersection.
    tiles_in_rect = set()
    for x in range(min_wx, max_wx):
        for y in range(min_wy, max_wy):
            p = world_to_screen(x, y)
            px, py = p[0] + camera_x, p[1] + camera_y
            tile_points = [(px, py), (px + cam_config.TILE_WIDTH // 2, py + cam_config.TILE_HEIGHT // 2), (px, py + cam_config.TILE_HEIGHT), (px - cam_config.TILE_WIDTH // 2, py + cam_config.TILE_HEIGHT // 2)]
            if selection_rect.collidepoint(tile_points[0]) or any(selection_rect.clipline(tile_points[i], tile_points[(i + 1) % 4]) for i in range(4)):
                tiles_in_rect.add((x, y))
    return tiles_in_rect

# ---- Initialize pygame ----
pygame.init()
window_size = (cam_config.SCREEN_WIDTH, cam_config.SCREEN_HEIGHT)
screen = pygame.display.set_mode(window_size)
BG_COLOR = (87, 87, 87)
pygame.display.set_caption("Isometric World with River Tile and Human")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# Main loop
running_game = True
camera_x, camera_y = 0,0

time_samples = []
import time
while running_game:
    dt = clock.get_time() / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running_game = False

    keys = pygame.key.get_pressed()

    camera.control(dt, keys=keys)

    if keys[pygame.K_q]:
        running_game = False


    screen.fill(BG_COLOR)

    # --- Find tiles inside the red rectangle ---
    rect_width, rect_height = cam_config.SCREEN_WIDTH // 2, cam_config.SCREEN_HEIGHT // 2
    rect_x = (window_size[0] - rect_width) // 2
    rect_y = (window_size[1] - rect_height) // 2
    red_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

    t0 = time.perf_counter()
    tiles_in_rect = camera.get_tiles_in_rect(red_rect)
    dt = (time.perf_counter() - t0) * 1000
    print(f"{dt:.6f}\n")

    time_samples.append(dt)


    # Draw a grid of blue lines
    grid_width = world_config.WIDTH
    grid_height = world_config.HEIGHT
    tile_width = cam_config.TILE_WIDTH
    tile_height = cam_config.TILE_HEIGHT
    blue_color = (0, 0, 255)

    if True: # Draw full grid for testing
        for x in range(grid_width):
            for y in range(world_config.HEIGHT):
                p = world_to_screen(x, y)
                px, py = p[0],p[1]
                px += camera.x
                py += camera.y

                # Define the four corners of the isometric tile
                points = [
                    (px, py),  # Top corner
                    (px + tile_width // 2, py + tile_height // 2),  # Right corner
                    (px, py + tile_height),  # Bottom corner
                    (px - tile_width // 2, py + tile_height // 2)   # Left corner
                ]
                pygame.draw.polygon(screen, blue_color, points, 1) # Draw outline for others

    for (x, y) in tiles_in_rect:
        p = world_to_screen(x, y)
        px, py = p[0],p[1]
        px += camera.x
        py += camera.y

        # Define the four corners of the isometric tile
        points = [
            (px, py),  # Top corner
            (px + tile_width // 2, py + tile_height // 2),  # Right corner
            (px, py + tile_height),  # Bottom corner
            (px - tile_width // 2, py + tile_height // 2)   # Left corner
        ]

        pygame.draw.polygon(screen, (0, 100, 255), points, 0) # Fill selected tiles


    # Draw a red rectangle with scaled screen size at the center of the screen
    pygame.draw.rect(screen, (255, 0, 0), red_rect, 2)

    # camera.FPS counter
    fps_text = pygame.font.SysFont(None, 24).render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
    screen.blit(fps_text, (window_size[0] - 150, window_size[1] - 30))

    pygame.display.flip()
    clock.tick()

pygame.quit()

import matplotlib.pyplot as plt
plt.hist(time_samples, bins=30, edgecolor='black')
plt.savefig("tile_selection.png")