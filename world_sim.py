import pygame
import logging

import controls
from world_object import WorldObject
from world import World
from camera import Camera
from rendering import Layer
from minimap import MiniMap
from character import Human

from manager import Manager, SelectionManager
from pygame_interface import PGISelectionController
from pygame_interface import PGICameraControl

# --- Logging setup ---
logger = logging.getLogger(__name__)
PROJECT_PREFIXES = ("world", "terrain", "pgi", "manager")
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
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 1000
WORLD_WIDTH, WORLD_HEIGHT = 100, 100

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

# --- Initialize Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile-Based Survival Game")
clock = pygame.time.Clock()

# --- Camera ---
camera = Camera(world=my_world, x=0, y=0, width_pxl=SCREEN_WIDTH, height_pxl=SCREEN_HEIGHT)
camera_control = PGICameraControl(camera=camera)
# --- Minimap ---
minimap = MiniMap(my_world, camera, size=200, position=(SCREEN_WIDTH - 210, 10))
#  Dummy objects
class Dot:
    def __init__(self, x, y, color:tuple[int,int,int] = (0,0,0) ):
        self.x, self.y = x, y  # world coordinates (center of the dot)

    def render(self, surface, camera):
        # Convert world position to screen position
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)

        # Scale dot size: 0.5 tile in world units → pixels
        radius = int(0.25 * camera.tile_size)  # 0.5 diameter = 0.25 radius
        diameter = radius * 2

        # Offset so the circle is centered on the world position
        screen_x -= radius
        screen_y -= radius

        # Draw the circle
        pygame.draw.ellipse(surface, (255, 0, 0), (screen_x, screen_y, diameter, diameter))
red_dot = Dot(10,10, (255,0,0))
blu_dot = Dot(10,10, (0,0,255))

# --- Layers ---
layer_world_terrains = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)
layer_world_terrains.add(my_world)

layer_world_elements = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)
for agent in all_agents:
    layer_world_elements.add(agent)

layer_game_interface = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)

# --- Initialize Manager ---
manager = Manager(world=my_world, agents=all_agents)
manager.resume()

selection = SelectionManager()
pgi_selector = PGISelectionController(selection_manager=selection, camera=camera)

# --- Example objects ---
layer_game_interface.objects = manager.get_agents()

# --- Overlay ---
show_overlay = False

# --- Main loop ---
running = True
while running:
    events = pygame.event.get()

    # update selection
    pgi_selector.handle_events(events, manager.get_agents())

    # Control camera
    camera_control.handle_actions()

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

    # Click on minimap handling
    if pygame.mouse.get_pressed()[0]:
        minimap.handle_click(pygame.mouse.get_pos())

    # Update the world and agents
    manager.update()  # dt calculated automatically

    for agent in manager.get_agents():
        color = (0,222,0) if agent.id in selection.selected else (200,20,20)
        agent.dummy_render_color = color

    # --- Render ---
    layer_world_terrains.draw(camera)
    layer_world_elements.draw(camera)
    layer_game_interface.draw(camera)

    pgi_selector.draw_drag_box(layer_game_interface.surface)

    # --- Composite layers ---
    screen.blit(layer_world_terrains.surface, (0, 0))
    screen.blit(layer_world_elements.surface, (0, 0))
    screen.blit(layer_game_interface.surface, (0, 0))


    # Draw minimap on screen
    screen.blit(minimap.render(), minimap.position)
    text_surface = pygame.font.SysFont(None, 40).render(f"{manager.days:.2f}", True, (255,0,0))
    screen.blit(text_surface, (0, 0))

    # --- Overlay ---
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
