import pygame
import random
from src.map_data import Terrain, Resource, generate_terrain_map, place_resources
from src.character import RandomCharacter
from src.spawn import find_spawn_point
from src.render_map import render_map

# --- Pygame setup ---
pygame.init()
MAP_WIDTH, MAP_HEIGHT = 100, 100  # map in tiles
WINDOW_WIDTH, WINDOW_HEIGHT = 1024, 780  # screen size in pixels
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()

# --- Camera ---
camera_x, camera_y = 0, 0
CAMERA_SPEED = 300
MIN_TILE_SIZE, MAX_TILE_SIZE = 1, 64

# --- Terrains and resources ---
wood = Resource("wood", (139,69,19))
stone = Resource("stone", (160,160,160))
food = Resource("food", (255,255,0))

terrains = {
    "water": Terrain("water", color=(0,0,255)),
    "grass": Terrain("grass", color=(0,255,0), resources=[wood,food]),
    "forest": Terrain("forest", color=(34,139,34), resources=[wood,food]),
    "mountain": Terrain("mountain", color=(139,137,137), resources=[stone])
}

fractions = {
    "water": 0.2,
    "grass": 0.4,
    "forest": 0.3,
    "mountain": 0.1
}

# --- Generate map ---
map_grid = generate_terrain_map(MAP_WIDTH, MAP_HEIGHT, terrains=terrains, terrain_fractions=fractions, seed=42)
map_grid = place_resources(map_grid, num_resources=100)  # large map

# --- Characters ---
walker = RandomCharacter(speed=5, blocked_terrains=["water","mountain"])
walker.x, walker.y = find_spawn_point(walker, map_grid)
flyer  = RandomCharacter(speed=8, blocked_terrains=["mountain"])
flyer.x, flyer.y = find_spawn_point(flyer, map_grid)
characters = [walker, flyer]


# --- Main loop ---
running = True
TILE_SIZE = MIN_TILE_SIZE
while running:
    dt = clock.tick(60)/1000

    # --- Events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEWHEEL:
            TILE_SIZE += event.y * 2
            TILE_SIZE = max(MIN_TILE_SIZE, min(MAX_TILE_SIZE, TILE_SIZE))

    # --- Camera control ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]: camera_x -= CAMERA_SPEED*dt
    if keys[pygame.K_d]: camera_x += CAMERA_SPEED*dt
    if keys[pygame.K_w]: camera_y -= CAMERA_SPEED*dt
    if keys[pygame.K_s]: camera_y += CAMERA_SPEED*dt

    # Clamp camera
    max_cam_x = MAP_WIDTH*TILE_SIZE - WINDOW_WIDTH
    max_cam_y = MAP_HEIGHT*TILE_SIZE - WINDOW_HEIGHT
    camera_x = max(0, min(max_cam_x, camera_x))
    camera_y = max(0, min(max_cam_y, camera_y))

    # --- Update characters ---
    for c in characters:
        c.move_randomly(map_grid, dt)

    # --- Render map ---
    TILE_SIZE = render_map(screen, map_grid, characters, camera_x, camera_y, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_TILE_SIZE, MAX_TILE_SIZE)

    pygame.display.flip()

pygame.quit()
