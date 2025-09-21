import controls
import overlays
from world import World, WorldGen, WorldGenConfig
from camera import CameraIso, CameraIsoConfig
import pygame, random, os
from pathlib import Path
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
world_config = WorldGenConfig(  SIZE_X= 40,
                                SIZE_Y= 40,
                                SCALE = 10,
                                TILE_SUBDIVISIONS=1,
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
        screen_height = 1000,
        tile_width = 64,
        tile_height = 32
    )
camera = CameraIso(my_world, 0, 0, config=cam_config)

# Parameters
TILE_SCALE = 0.5 # Tiles per meter
BG_COLOR = (30, 30, 30)

# Initialize pygame
pygame.init()
window_size = (camera.config.SCREEN_WIDTH, camera.config.SCREEN_HEIGHT)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Isometric World with River Tile and Human")
clock = pygame.time.Clock()

# Load textures
TILE_TEXTURES:dict[str,list[pygame.Surface]] = {
    "ocean" : [],
    "lake" : [],
    "river" : [],
    "beach" : [],
    "grassland" : [],
    "forest" : [],
    "mountain" : [],
    "ice_cap" : [],
    "pond" : []
}
for terrain in TILE_TEXTURES.keys():
    terrain_dir = f"./textures/terrains/{terrain}"
    for filename in os.listdir(terrain_dir):
        if filename.lower().endswith(".png"):
            path = os.path.join(terrain_dir, filename)
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (camera.tile_width_pxl, camera.tile_height_pxl * 2))
            # img.set_colorkey((0, 0, 0))
            TILE_TEXTURES[terrain].append(img)
    if not TILE_TEXTURES[terrain]:
        raise RuntimeError(f"No PNG tiles found in {terrain_dir}")

ELEMENT_TEXTURES: dict[str,dict[tuple[int,int]]] = {
    "trees": {},
    "stones": {}
}

def hash_to_tuple(s: str, n: int = 2) -> tuple[int, ...]:
    h = hash(s)
    h &= (1 << (32 * n)) - 1
    result = tuple((h >> (32 * i)) & 0xFFFFFFFF for i in reversed(range(n)))
    return result

def key_from_texture(texture_path:str) -> tuple[int,int] | None:
    name, _ = os.path.splitext(texture_path)
    try:
        model, lifecycle = map(int, name.split("."))
        return model,lifecycle
    except ValueError:
        return hash_to_tuple(texture_path)

for element in ELEMENT_TEXTURES.keys():
    element_dir = f"./textures/elements/{element}"
    for filename in os.listdir(element_dir):
        if filename.lower().endswith(".png"):
            key = key_from_texture(filename)
            path = os.path.join(element_dir, filename)
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (2*camera.tile_height_pxl,2*camera.tile_height_pxl))
            ELEMENT_TEXTURES[element][key] = img




# Directory containing tile images
character_dir = "./textures/agents/male_human/animations/"
direction_v2str = {
            (-1, -1): 'north',
            (1, -1): 'east',
            (1, 1): 'south',
            (-1, 1): 'west',
            (0, -1): 'north-east',
            (1, 0): 'south-east',
            (0, 1): 'south-west',
            (-1, 0): 'north-west'
        }
# --- Human class ---
class Human:
    def __init__(self, base_dir, walk_type='walking-8-frames', run_type='running-8-frames', start_pos:tuple[float,float] | None = None, frame_delay=5, size=(50,50)):
        self.walking_animations = self.load_animations(base_dir, walk_type, size)
        self.running_animations = self.load_animations(base_dir, run_type, size)
        self.current_animations = self.walking_animations
        self.direction = 'south'
        self.frame_index = 0
        self.frame_counter = 0
        self.frame_delay = frame_delay

        if start_pos is not None:
            self.x, self.y = start_pos  # world coordinates in fractional tile units

        self.walk_speed = 0.4*TILE_SCALE  # tiles per second
        self.run_speed  = 1.6*TILE_SCALE  # tiles per second

    def load_animations(self, base_dir, animation_type, size) -> dict[str, list[pygame.Surface]]:
        animations = {}
        anim_dir = os.path.join(base_dir, animation_type)
        for direction in os.listdir(anim_dir):
            dir_path = os.path.join(anim_dir, direction)
            if os.path.isdir(dir_path):
                frames = []
                for file_name in sorted(os.listdir(dir_path)):
                    if file_name.lower().endswith('.png'):
                        img = pygame.image.load(os.path.join(dir_path, file_name)).convert_alpha()
                        img = pygame.transform.scale(img, size)
                        frames.append(img)
                animations[direction] = frames
        return animations

    def update(self, dt, keys = None, events=None, mouse_pos=None):
        # Map WASD to isometric grid deltas (screen-relative)

        moving = False
        speed = self.walk_speed

        # Running vs walking
        if keys:
            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and (keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]):
                self.current_animations = self.running_animations
                speed = self.run_speed
            else:
                self.current_animations = self.walking_animations
                speed = self.walk_speed

            dx = 0
            dy = 0
            # WASD to isometric 8-direction movement
            if keys[pygame.K_w] and keys[pygame.K_a]:
                dx -= 1
                dy += 0
            elif keys[pygame.K_w] and keys[pygame.K_d]:
                dx += 0
                dy -= 1
            elif keys[pygame.K_s] and keys[pygame.K_a]:
                dx -= 0
                dy += 1
            elif keys[pygame.K_s] and keys[pygame.K_d]:
                dx += 1
                dy += 0
            elif keys[pygame.K_w]:
                dx -= 1
                dy -= 1
            elif keys[pygame.K_s]:
                dx += 1
                dy += 1
            elif keys[pygame.K_a]:
                dx -= 1
                dy += 1
            elif keys[pygame.K_d]:
                dx += 1
                dy -= 1

            if dx != 0 or dy != 0:
                norm = (dx ** 2 + dy ** 2) ** 0.5
                self.x += (dx / norm) * speed*dt
                self.y += (dy / norm) * speed*dt
                moving = True
                dir_tuple = (int(round(dx)), int(round(dy)))
                if dir_tuple in direction_v2str:
                    self.direction = direction_v2str[dir_tuple]

            # Update animation frame
            if moving:
                self.frame_counter += 1
                if self.frame_counter >= self.frame_delay:
                    self.frame_index = (self.frame_index + 1) % len(self.current_animations[self.direction])
                    self.frame_counter = 0
            else:
                self.frame_index = 0

    def draw(self, surface, cam_x, cam_y):
        # Convert world coordinates to pixel coordinates
        px,py = camera.world_to_pixel(self.x, self.y)

        img = self.current_animations[self.direction][self.frame_index]
        surface.blit(img, (px + cam_x - img.get_width()//2, py + cam_y - img.get_height()))

# --- Initialize character ---
char_start_pos = (my_world.size_x // 2, my_world.size_y // 2)
character = Human(character_dir, start_pos=char_start_pos,frame_delay=camera.FPS/8)


# --- Generate world ---
my_world.generate()

# Create world surface
world_surface = pygame.Surface((camera.world_width_pxl, camera.world_height_pxl + camera.iso_offset_y + camera.tile_height_pxl), pygame.SRCALPHA)


sorted_z = []
for s in range(my_world.elements.shape[0] + my_world.elements.shape[1] - 1):  # sum of indices
    for y in range(my_world.elements.shape[1]):
        x = s - y
        if 0 <= x < my_world.elements.shape[0]:
            sorted_z.append((x,y))

# Compute isometric offset for world_surface
for col, row in sorted_z[:my_world.size_x * my_world.size_y]:
    current_tile = my_world.get_tile(col, row)
    # Isometric local coordinates for world_surface
    x, y = camera.world_to_pixel(col, row)

    # Select a tile image from the correct terrain
    terrain_name = current_tile.terrain.name
    tile_imgs = TILE_TEXTURES.get(terrain_name)
    if not tile_imgs:
        raise RuntimeError(f"No textures loaded for terrain '{terrain_name}'")
    img = random.choice(tile_imgs)

    # Apply water offset if needed
    if current_tile.is_water:
        tile_offset_y = camera.tile_height_pxl // 2
    elif current_tile.terrain.name in ["mountain", "ice_cap"]:
        tile_offset_y = 0
    else:
        tile_offset_y = 0

    # Blit tile to world surface
    world_surface.blit(img, (int(x), int(y + tile_offset_y)))

# Draw a red border around the world_surface
border_rect = world_surface.get_rect()
pygame.draw.rect(world_surface, (255, 0, 0), border_rect, 3)

# --- Create a cached grid surface ---
# Pre-render the grid once
grid_surface = overlays.draw_grid(
    my_world.size_x, my_world.size_y, camera.tile_width_pxl, camera.tile_height_pxl,
    offset_x=camera.tile_width_pxl//2,
    color=(0, 0, 0, 100),
    grid_to_iso=camera.world_to_screen
)
world_with_grid_surface = world_surface.copy()
world_with_grid_surface.blit(grid_surface, (0, 0))

# Add trees
world_elements = pygame.sprite.LayeredUpdates()
def generate_trees_surface(world:World, trees_dict:dict[tuple[int,int],pygame.Surface], tile_w, tile_h):
    """
    Generate a surface with trees based on the World.elements array.

    Only places one tree per tile cell that has a Tree object.
    """
    grid_w = world.size_x
    grid_h = world.size_y
    N = world.gen.config.TILE_SUBDIVISIONS

    world_w = (grid_w + grid_h) * (tile_w // 2)
    world_h = (grid_w + grid_h) * (tile_h // 2) + tile_h*2
    surface = pygame.Surface((world_w, world_h), pygame.SRCALPHA)

    for row in range(world.elements.shape[0]):
        for col in range(world.elements.shape[1]):
            t = world.elements[row, col]
            if t is None:
                continue

            key = key_from_texture(Path(t.texture).name)
            tree_img = trees_dict[key]

            # Compute tile coordinates
            tile_x = col / N
            tile_y = row / N

            iso_x, iso_y = camera.world_to_screen(tile_x, tile_y)
            tile_center_x = iso_x + tile_w // 2
            tile_center_y = iso_y + tile_h // 2

            pos_x = tile_center_x - tree_img.get_width() // 2
            pos_y = tile_center_y - tree_img.get_height()
            surface.blit(tree_img, (pos_x, pos_y))

    return surface


tree_surface = generate_trees_surface(
    my_world,
    trees_dict=ELEMENT_TEXTURES["trees"],
    tile_w=camera.tile_width_pxl,
    tile_h=camera.tile_height_pxl
)

def front_cone(world_x:float, world_y:float) -> list[tuple[int,int]]:
    cone = [
        (int(world_x) + 0, int(world_y) + 0),
        (int(world_x) + 0, int(world_y) + 1),
        (int(world_x) + 1, int(world_y) + 0),
        (int(world_x) + 1, int(world_y) + 1),
        (int(world_x) + 0, int(world_y) + 2),
        (int(world_x) + 2, int(world_y) + 0),
        (int(world_x) + 2, int(world_y) + 1),
        (int(world_x) + 1, int(world_y) + 2),
        (int(world_x) + 0, int(world_y) + 3),
        (int(world_x) + 3, int(world_y) + 0),
    ]
    return cone

# Camera position
camera_speed = 8
font = pygame.font.SysFont(None, 24)

import numpy as np

def get_visible_tiles_vectorized(world, camera, offset_x=0, offset_y=0):
    """
    Return a list of tiles that are at least partially visible in camera view, using CameraIso.
    offset_x, offset_y: the offset used when blitting the world surface.
    """
    screen_w = camera.screen_width
    screen_h = camera.screen_height

    # Adjust screen corners by the offset
    corners_screen = [
        (0 - offset_x, 0 - offset_y),  # Top-left
        (screen_w - offset_x, 0 - offset_y),  # Top-right
        (0 - offset_x, screen_h - offset_y),  # Bottom-left
        (screen_w - offset_x, screen_h - offset_y)  # Bottom-right
    ]
    corners_world = [camera.screen_to_world(sx, sy) for sx, sy in corners_screen]

    xs = [wx for wx, wy in corners_world]
    ys = [wy for wx, wy in corners_world]

    margin = 3
    min_x = max(0, int(np.floor(min(xs))) - margin)
    max_x = min(world.size_x - 1, int(np.ceil(max(xs))) + margin)
    min_y = max(0, int(np.floor(min(ys))) - margin)
    max_y = min(world.size_y - 1, int(np.ceil(max(ys))) + margin)

    visible_tiles = []
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            points = [
                camera.world_to_screen(x, y),
                camera.world_to_screen(x + 1, y),
                camera.world_to_screen(x, y + 1),
                camera.world_to_screen(x + 1, y + 1),
                camera.world_to_screen(x + 0.5, y + 0.5),
            ]
            # Add the offset back to the screen coordinates
            if any(
                0 <= sx + offset_x < screen_w and 0 <= sy + offset_y < screen_h
                for sx, sy in points
            ):
                visible_tiles.append((x, y))

    return visible_tiles

# Main loop
running_game = True
while running_game:
    dt = clock.get_time() / 1000
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running_game = False
        elif event.type == pygame.KEYDOWN:
            if event.key == controls.OVERLAY_GRID_KEY:
                overlays.SHOW_GRID = not overlays.SHOW_GRID  # toggle grid visibility

    keys = pygame.key.get_pressed()

    n_of_visible_tiles = len(get_visible_tiles_vectorized(my_world, camera))
    # print(f"Visible tiles: {len(n_of_visible_tiles)}")

    # Camera movement
    camera.control(dt,keys=keys)

    # Update character
    character.update(dt,keys)
    screen.fill(BG_COLOR)

    offset_x, offset_y = camera.world_to_screen(0, 0)

    if overlays.SHOW_GRID:
        screen.blit(world_with_grid_surface, (offset_x, offset_y))
    else:
        screen.blit(world_surface, (offset_x, offset_y))

    # ------------------------------------------------------
    """
    Draw a red ball at world coordinates (tiles) on the given surface.
    """
    # Draw red circle
    pygame.draw.circle(world_surface, (255, 0, 0), (camera.world_to_pixel(0.5,0)), 10)
    pygame.draw.circle(world_surface, (255, 0, 0), (camera.world_to_pixel(0.5,my_world.size_y)), 10)
    pygame.draw.circle(world_surface, (255, 0, 0), (camera.world_to_pixel(0.5+my_world.size_x,0)), 10)
    pygame.draw.circle(world_surface, (255, 0, 0), (camera.world_to_pixel(0.5+my_world.size_x,my_world.size_y)), 10)
    # ------------------------------------------------------
    character.draw(screen, offset_x, offset_y)

    screen.blit(tree_surface, (offset_x, offset_y))


    # camera.FPS counter
    fps_text = pygame.font.SysFont(None, 24).render(f"{n_of_visible_tiles}:FPS: {int(clock.get_fps())}", True, (255, 255, 255))
    screen.blit(fps_text, (window_size[0] - 150, window_size[1] - 30))

    pygame.display.flip()
    clock.tick()

pygame.quit()
