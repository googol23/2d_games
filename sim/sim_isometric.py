import pygame
import sys
import random
import glob
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Tile size
TILE_WIDTH = 128
TILE_HEIGHT = 64

# Load your tile texture (with transparent background)
textures = []
for filename in sorted(glob.glob("textures/grass*.png")):
    tile_texture = pygame.image.load(filename).convert_alpha()
    textures.append(pygame.transform.scale(tile_texture, (TILE_WIDTH, TILE_HEIGHT)))


# Converts grid coordinates to isometric screen coordinates
def grid_to_iso(x, y):
    px = (x - y) * (TILE_WIDTH // 2) + 400  # offset to center
    py = (x + y) * (TILE_HEIGHT // 2) + 50
    return px, py

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((30, 30, 30))

    # Draw a 10x10 grid of tiles using the texture
    for x in range(10):
        for y in range(10):
            px, py = grid_to_iso(x, y)
            # Draw the tile image centered at the calculated position
            screen.blit(random.choice(textures), (px - TILE_WIDTH // 2, py))

    pygame.display.flip()
    clock.tick(60)
