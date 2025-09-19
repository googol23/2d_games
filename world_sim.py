from tree import load_trees
from terrain import load_terrains_data
from world import World, WorldGen, WorldGenConfig
from minimap import MiniMap

import traceback
import pygame
import logging
import sys
import threading

import controls
from camera import Camera
from rendering import Layer
from character import Human

from manager import Manager
from pygame_interface import PGISelectionController
from pygame_interface import PGICameraControl
from pygame_interface import PGIAgentControl
from pygame_interface import PGIAgentPathPainter
from pygame_interface import PGIWorldPainter
from pygame_interface import PGIWorldObjectSetPainter
# --- Logging setup ---
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

# --- Configuration ---
FPS = 120
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 1000
WORLD_WIDTH, WORLD_HEIGHT = 160, 100

# --- Initialize world ---
world_config = WorldGenConfig(  SIZE_X= 50,
                                SIZE_Y= 50,
                                SCALE = 10,
                                TILE_SUBDIVISIONS=4,
                                WATER_RATIO=0.15,
                                MOUNTAIN_RATIO=0.15,
                                ICE_CAP_RATIO=0.01
                              )
world_gentor = WorldGen(config=world_config)
World(world_gentor).generate()

# --- Initialize agents ---
rowan = Human("Rowan", age=20)
clara = Human("Clara", age=20)
rowan.x, rowan.y = 10, 10
clara.x, clara.y = 20, 20


# --- Initialize Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("DPEPDPEC")
clock = pygame.time.Clock()

# --- Camera ---
camera = Camera(x=0, y=0, width_pxl=SCREEN_WIDTH, height_pxl=SCREEN_HEIGHT)

# --- Minimap ---
minimap = MiniMap(size=SCREEN_WIDTH//8, position=(SCREEN_WIDTH - 200, 10))

# --- Initialize Manager ---
manager = Manager(agents=[rowan,clara])

# --- Layers ---
surface_world_terrains = pygame.Surface((camera.width_pxl,camera.height_pxl), pygame.SRCALPHA)
surface_world_elements = pygame.Surface((camera.width_pxl,camera.height_pxl), pygame.SRCALPHA)
surface_game_interface = pygame.Surface((camera.width_pxl,camera.height_pxl), pygame.SRCALPHA)

# ---- Sprite Groups and Painters ----
world_painter = PGIWorldPainter()
elemt_painter = PGIWorldObjectSetPainter(manager = manager)
paths_painter = PGIAgentPathPainter(manager=manager)


# --- Pygame interfaceing ---
camera_control = PGICameraControl()
pgi_selector = PGISelectionController(selection_manager=manager.selection)
agent_controler = PGIAgentControl(manager=manager)


# --- Overlay ---
show_overlay = False

# --- Main loop ---
try:
    manager.resume()
    running = True
    while running:
        screen.fill((0, 0, 0))  # clear the screen each frame
        surface_world_terrains.fill((0, 0, 0, 0))
        surface_world_elements.fill((0, 0, 0, 0))
        surface_game_interface.fill((0, 0, 0, 0))

        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == controls.TOGGLE_OVERLAY_KEY:
                    show_overlay = not show_overlay
                if event.key == controls.REGENERATE_WORLD_KEY:
                    World.get_instance().generate()
                    minimap.needs_redraw = True
                    world_painter.reset()
                    manager.reset()
                if event.key == controls.PAUSE_GAME_KEY:
                    manager.toggle_pause()
                    print("game paused" if manager.paused else "game resumed")

        # update selection
        pgi_selector.handle_events(events, manager.get_agents())
        agent_controler.command_agents(events)

        # Update the world and agents
        manager.update()  # dt calculated automatically

        # Control camera
        camera_control.handle_actions(events,keys,mouse_pos)

        # Minimap handling
        if pygame.mouse.get_pressed()[0]:
            minimap.handle_click(pygame.mouse.get_pos())

        # --- Render ---
        world_painter.update()
        elemt_painter.update()

        world_painter.draw(surface_world_terrains)
        elemt_painter.draw(surface_world_elements)

        pgi_selector.draw_drag_box(surface_game_interface)
        paths_painter.draw(surface_game_interface)
        minimap.draw(surface_game_interface)

        # --- Composite layers ---
        screen.blit(surface_world_terrains, (0, 0))
        screen.blit(surface_world_elements, (0, 0))
        screen.blit(surface_game_interface, (0, 0))


        text_surface = pygame.font.SysFont(None, 40).render(f"Days: {manager.days:.2f}", True, (255,0,0))
        screen.blit(text_surface, (0, 0))

        # Monitor FPS
        fps_text = pygame.font.SysFont(None, 24).render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
        rect = pygame.Rect(SCREEN_WIDTH - 90, SCREEN_HEIGHT-40, 80, 30)
        pygame.draw.rect(screen, (0, 0, 0), rect)
        screen.blit(fps_text, (SCREEN_WIDTH - 80, SCREEN_HEIGHT-30))

        # --- Overlay ---
        pygame.display.flip()
        clock.tick(FPS)
except Exception as e:
    print(e)
    traceback.print_exc()
    pygame.event.clear()
    pygame.quit()
    sys.exit()
finally:
    pygame.event.clear()
    pygame.quit()
    sys.exit()
