import pygame
import random
from src.map_data import Terrain, Resource, generate_terrain_map, place_resources
from src.character import RandomCharacter

# --- Pygame setup ---
pygame.init()
WIDTH, HEIGHT = 640, 480
TILE_SIZE = 32
GRID_WIDTH, GRID_HEIGHT = WIDTH//TILE_SIZE, HEIGHT//TILE_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# --- Define terrains and resources ---
wood = Resource("wood",(139,69,19))
stone = Resource("stone",(160,160,160))
food = Resource("food",(255,255,0))

grass = Terrain("grass",(0,200,0),[wood,food])
water = Terrain("water",(0,0,200),[])
mountain = Terrain("mountain",(100,100,100),[stone])

terrains = {"grass":grass,"water":water,"mountain":mountain}

# --- Generate map ---
map_grid = generate_terrain_map(GRID_WIDTH, GRID_HEIGHT, scale=0.1, terrains=terrains)
map_grid = place_resources(map_grid, num_resources=60)

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
    px = gx * TILE_SIZE + TILE_SIZE / 2
    py = gy * TILE_SIZE + TILE_SIZE / 2
    return px, py

# --- Create characters ---
walker = RandomCharacter(WIDTH//2, HEIGHT//2, speed=120, blocked_terrains=["water","mountain"])
walker.x, walker.y = find_spawn_point(walker, map_grid)
flyer  = RandomCharacter(WIDTH//4, HEIGHT//4, speed=150, blocked_terrains=["mountain"])
flyer.x, flyer.y = find_spawn_point(flyer, map_grid)
characters = [walker, flyer]

# --- Main loop ---
running = True
while running:
    dt = clock.tick(60)/1000
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False

    # --- Update characters ---
    for c in characters:
        c.move_randomly(map_grid, dt, TILE_SIZE)

    # --- Draw ---
    screen.fill((0,0,0))
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            tile = map_grid[y][x]
            pygame.draw.rect(screen, tile.terrain.color,
                             pygame.Rect(x*TILE_SIZE,y*TILE_SIZE,TILE_SIZE,TILE_SIZE))
            if tile.resource:
                pygame.draw.circle(screen, tile.resource.color,
                                   (x*TILE_SIZE+TILE_SIZE//2, y*TILE_SIZE+TILE_SIZE//2),
                                   TILE_SIZE//4)

    for c in characters:
        c.draw(screen)

    pygame.display.flip()

pygame.quit()
