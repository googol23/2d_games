import traceback
import pygame
import logging
import sys

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
from pygame_interface import PGIAgentControl
from pygame_interface import PGIAgentPathPainter

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
rowan = Human("Rowan", age=20,health=100,speed=1.5)
clara = Human("Clara", age=20,health=100,speed=1.5)
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

# --- Initialize Manager ---
manager = Manager(world=my_world, agents=all_agents)

# --- Layers ---
layer_world_terrains = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)
layer_world_terrains.add(my_world)

layer_world_elements = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)
for agent in all_agents:
    layer_world_elements.add(agent)

layer_game_interface = Layer(SCREEN_WIDTH, SCREEN_HEIGHT, transparent=True)
layer_game_interface.add(PGIAgentPathPainter(manager=manager))

pgi_selector = PGISelectionController(selection_manager=manager.selection, camera=camera)
agent_controler = PGIAgentControl(manager=manager,camera=camera)

# --- Overlay ---
show_overlay = False

# --- Main loop ---
try:
    manager.resume()
    running = True
    while running:
        events = pygame.event.get()


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

        # update selection
        pgi_selector.handle_events(events, manager.get_agents())
        agent_controler.command_agents(events)

        # Control camera
        camera_control.handle_actions()

        # Click on minimap handling
        if pygame.mouse.get_pressed()[0]:
            minimap.handle_click(pygame.mouse.get_pos())

        # Update the world and agents
        manager.update()  # dt calculated automatically

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
except Exception as e:
    print(e)
    pygame.quit()
    traceback.print_exc()
    sys.exit()
finally:
    pygame.quit()
    sys.exit()
