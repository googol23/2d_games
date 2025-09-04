import pygame
import sys
import matplotlib.cm as cm
import numpy as np

from world import find_path, WorldObject, World

from rendering import Camera, Layer

import logging
logger = logging.getLogger(__name__)
PROJECT_PREFIXES=("world", "terrain")
# Create a handler and formatter
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Iterate over all existing loggers
for name, logger_obj in logging.root.manager.loggerDict.items():
    if isinstance(logger_obj, logging.Logger) and name.startswith(PROJECT_PREFIXES):
        logger_obj.addHandler(ch)
        logger_obj.setLevel(logging.DEBUG)


# --- Configuration ---
TILE_SIZE = 10  # base tile size in pixels
FPS = 60
SPEED = 5  # tiles/sec

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 1000  # display resolution

# --- Generate World map ---
my_world = World(100,100)
my_world.generate()


import pygame

# Initialize Pygame
pygame.init()

# Screen size
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tile-Based Survival Game")
clock = pygame.time.Clock()

# Tile size
TILE_SIZE = 5

# Initialize camera
camera = Camera(0, 0, WIDTH, HEIGHT, tile_size=TILE_SIZE)

# Initialize layers
objects_layer = Layer(WIDTH, HEIGHT, transparent=True)  # trees, stones, resources
movables_layer = Layer(WIDTH, HEIGHT, transparent=True) # player, enemies

# Example objects
# You can replace images with pygame.Surface or load images
objects_layer.add(WorldObject(2, 2))  # a tree
movables_layer.add(WorldObject(5, 5))   # player


running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Example player movement (arrow keys)
    keys = pygame.key.get_pressed()
    player = movables_layer.objects[0]
    moved = False
    if keys[pygame.K_LEFT]:
        player.x -= 1
        moved = True
    if keys[pygame.K_RIGHT]:
        player.x += 1
        moved = True
    if keys[pygame.K_UP]:
        player.y -= 1
        moved = True
    if keys[pygame.K_DOWN]:
        player.y += 1
        moved = True
    if moved:
        player.needs_redraw = True

    # Draw all layers
    world_surface = my_world.render(pygame.Surface((WIDTH, HEIGHT)), camera)
    objects_layer.draw(camera)
    movables_layer.draw(camera)

    # Composite layers to screen
    screen.blit(objects_layer.surface, (0, 0))
    screen.blit(movables_layer.surface, (0, 0))

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()