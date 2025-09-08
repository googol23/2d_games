import pygame
import logging
from world import WorldObject, World
from rendering import Camera, Layer

# --- Logging setup ---
logger = logging.getLogger(__name__)
PROJECT_PREFIXES = ("world", "terrain")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
for name, log_obj in logging.root.manager.loggerDict.items():
    if isinstance(log_obj, logging.Logger) and name.startswith(PROJECT_PREFIXES):
        log_obj.addHandler(ch)
        log_obj.setLevel(logging.DEBUG)

# --- Configuration ---
FPS = 60
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 720
WORLD_WIDTH, WORLD_HEIGHT = 1000, 1000
TILE_SIZE = 5
CAMERA_SPEED_TILES = 100       # Tiles per frame
ZOOM_STEP = 2
MIN_TILE_SIZE = 1
MAX_TILE_SIZE = 100

# --- Generate world ---
my_world = World(WORLD_WIDTH, WORLD_HEIGHT)
my_world.generate()

# --- Initialize Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile-Based Survival Game")
clock = pygame.time.Clock()

# --- Camera ---
camera = Camera(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, tile_size=TILE_SIZE)

# --- Layers ---
world_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
objects_layer = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)
movables_layer = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)

# Example objects
objects_layer.add(WorldObject(2, 2))  # a tree
movables_layer.add(WorldObject(5, 5)) # player

# --- Main loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player = movables_layer.objects[0]

    # --- Player movement (arrow keys) ---
    player_moved = False
    if keys[pygame.K_LEFT]:
        player.x -= 1
        player_moved = True
    if keys[pygame.K_RIGHT]:
        player.x += 1
        player_moved = True
    if keys[pygame.K_UP]:
        player.y -= 1
        player_moved = True
    if keys[pygame.K_DOWN]:
        player.y += 1
        player_moved = True
    if player_moved:
        player.needs_redraw = True

    # --- Camera movement (WASD, in tiles) ---
    if keys[pygame.K_w]:
        camera.y -= CAMERA_SPEED_TILES
    if keys[pygame.K_s]:
        camera.y += CAMERA_SPEED_TILES
    if keys[pygame.K_a]:
        camera.x -= CAMERA_SPEED_TILES
    if keys[pygame.K_d]:
        camera.x += CAMERA_SPEED_TILES

    # --- Zoom in/out ---
    if keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]:
        camera.tile_size = min(camera.tile_size + ZOOM_STEP, MAX_TILE_SIZE)
    if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
        camera.tile_size = max(camera.tile_size - ZOOM_STEP, MIN_TILE_SIZE)

    # --- Regenerate world ---
    if keys[pygame.K_KP_ENTER]:
        my_world.generate()

    # --- Render ---
    world_surface.fill((0, 0, 0))
    my_world.render(world_surface, camera)
    objects_layer.draw(camera)
    movables_layer.draw(camera)

    # --- Composite layers ---
    screen.blit(world_surface, (0, 0))
    screen.blit(objects_layer.surface, (0, 0))
    screen.blit(movables_layer.surface, (0, 0))

    pygame.display.flip()
    clock.tick(FPS)  # Use FPS here

pygame.quit()
