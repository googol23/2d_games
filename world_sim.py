import pygame
import logging

import controls
from world_object import WorldObject
from world import World
from rendering import Camera, Layer
from minimap import MiniMap
from character import Human

from manager import Manager, SelectionManager
from pygame_interface import PygameSelectionController
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
WORLD_WIDTH, WORLD_HEIGHT = 100, 100
TILE_SIZE = 5
CAMERA_SPEED_TILES = 3       # reasonable speed
ZOOM_STEP = 2
MIN_TILE_SIZE = 1
MAX_TILE_SIZE = 100


# --- Initialize world ---
my_world = World(WORLD_WIDTH, WORLD_HEIGHT)
my_world.generate()

# --- Initialize agents ---
rowan = Human("Rowan", age=20,health=100,speed=1)
clara = Human("Clara", age=20,health=100,speed=1)
rowan.x, rowan.y = 10, 10
clara.x, clara.y = 20, 20

all_agents = [rowan, clara]
act_agents = []

# --- Initialize Manager ---
manager = Manager(world=my_world, agents=all_agents)
manager.resume()

selection = SelectionManager()
pygame_selector = PygameSelectionController(selection_manager=selection)

# --- Initialize Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile-Based Survival Game")
clock = pygame.time.Clock()

# --- Camera ---
camera = Camera(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, tile_size=TILE_SIZE)

# --- Minimap ---
minimap = MiniMap(my_world, camera, size=200, position=(SCREEN_WIDTH - 210, 10))

# --- Layers ---
world_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
objects_layer = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)
movables_layer = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)

# --- Example objects ---
objects_layer.objects = manager.static_objects
movables_layer.objects = manager.get_agents()

# --- Overlay ---
show_overlay = False

# --- Main loop ---
running = True
while running:
    events = pygame.event.get()

    # update selection
    pygame_selector.handle_events(events, manager.get_agents())

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == controls.TOGGLE_OVERLAY_KEY:
                show_overlay = not show_overlay
            if event.key == controls.REGENERATE_WORLD_KEY:
                my_world.generate()
            if event.key == controls.PAUSE_GAME_KEY:
                manager.toggle_pause()
                print("game paused" if manager.paused else "game resumed")


    keys = pygame.key.get_pressed()

    # --- Camera movement (WASD + mouse-edge) ---
    # WASD
    for key, (dx, dy) in controls.CAMERA_KEYS.items():
        if keys[key]:
            camera.x += dx * CAMERA_SPEED_TILES
            camera.y += dy * CAMERA_SPEED_TILES

    # Mouse-edge panning
    mouse_x, mouse_y = pygame.mouse.get_pos()
    camera.edge_pan(mouse_x, mouse_y)

    # --- Zoom ---
    if any(keys[key] for key in controls.ZOOM_IN_KEYS):
        camera.tile_size = min(camera.tile_size + ZOOM_STEP, MAX_TILE_SIZE)
    if any(keys[key] for key in controls.ZOOM_OUT_KEYS):
        camera.tile_size = max(camera.tile_size - ZOOM_STEP, MIN_TILE_SIZE)

    # Click on minimap handling
    if pygame.mouse.get_pressed()[0]:
        minimap.handle_click(pygame.mouse.get_pos())

    # Update the world and agents
    manager.update()  # dt calculated automatically

    for agent in manager.get_agents():
        color = (0,222,0) if agent.id in selection.selected else (200,20,20)
        agent.dummy_render_color = color

    # --- Render ---
    world_surface.fill((0, 0, 0))
    my_world.render(world_surface, camera)
    objects_layer.draw(camera)
    movables_layer.draw(camera)

    pygame_selector.draw_drag_box(movables_layer.surface)

    # --- Composite layers ---
    screen.blit(world_surface, (0, 0))
    screen.blit(objects_layer.surface, (0, 0))
    screen.blit(movables_layer.surface, (0, 0))


    text_surface = pygame.font.SysFont(None, 20).render(f"{manager.days:.2f}", True, (255,0,0))
    screen.blit(text_surface, (0, 0))

    # Draw minimap on screen
    screen.blit(minimap.draw(), minimap.position)

    # --- Overlay ---
    if show_overlay:
        overlay_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay_image.fill((255, 255, 255, 100))  # semi-transparent white overlay
        screen.blit(overlay_image, (0, 0))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
