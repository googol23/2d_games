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
world_config = WorldGenConfig(  WIDTH = 50,
                                HEIGHT= 50,
                                SCALE = 10,
                                TILE_SUBDIVISIONS=2,
                                WATER_RATIO=0.15,
                                MOUNTAIN_RATIO=0.15,
                                ICE_CAP_RATIO=0.01
                              )
world_gen = WorldGen(config=world_config)
my_world = World(world_gen)

# Camera configuration
cam_config = CameraIsoConfig(
        fps = 120,
        speed_tiles = 20,
        screen_with = 1600,
        screen_height = 900,
        tile_width = 128,
        tile_height = 64
    )
camera = CameraIso(my_world, 0, 0, config=cam_config)

# ---- Initialize pygame ----
pygame.init()
window_size = (camera.config.SCREEN_WIDTH, camera.config.SCREEN_HEIGHT)
screen = pygame.display.set_mode(window_size)
BG_COLOR = (87, 87, 87)
pygame.display.set_caption("Isometric World with River Tile and Human")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# ---- Load textures ----
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


# --- Human class ---
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

        self.walk_speed = 0.4*my_world.scale  # tiles per second
        self.run_speed  = 1.6*my_world.scale  # tiles per second

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
                dir_tuple = dx,dy
                if dir_tuple in direction_v2str:
                    self.direction = direction_v2str[dir_tuple]

                norm = (dx ** 2 + dy ** 2) ** 0.5
                self.frame_counter += dt # TODO this needs tunning
                self.move((dx / norm) * speed * dt, (dy / norm) * speed * dt)

        else:
            self.frame_index = 0

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

        # Update animation frame
        if self.frame_counter >= self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.current_animations[self.direction])
            self.frame_counter = 0


    def draw(self, surface, cam_x, cam_y):
        # Convert world coordinates to pixel coordinates
        px,py = camera.world_to_screen(self.x, self.y)

        img = self.current_animations[self.direction][self.frame_index]
        surface.blit(img, (px + cam_x - img.get_width()//2, py + cam_y - img.get_height()))

# --- Initialize character ---
character = Human(character_dir,
                  start_pos=(my_world.width // 2, my_world.height // 2),
                  frame_delay=0.01, # TODO this needs tunning
                  size=(camera.tile_width_pxl,camera.tile_width_pxl))

# --- Generate world ---
my_world.generate()

# ---- Compute positions and configure Sprites ----
# Tiles
layer_counter = 0
tile_sprites = pygame.sprite.LayeredUpdates()
for (x, y), tile in np.ndenumerate(my_world.tiles):
    # Isometric coordinates
    i, j = camera.world_to_screen(x, y)

    # Select a tile image from terrain
    terrain_name = tile.terrain.name
    tile_imgs = TILE_TEXTURES.get(terrain_name)
    if not tile_imgs:
        raise RuntimeError(f"No textures loaded for terrain '{terrain_name}'")
    img = random.choice(tile_imgs)

    # Configure Tile Sprite
    tile.image = img
    tile.rect = img.get_rect(center=(i, j))
    tile.layer = layer_counter

    tile_sprites.add(tile)
    layer_counter += 1

# Trees
tree_sprites = pygame.sprite.LayeredUpdates()
for (y, x), t in np.ndenumerate(my_world.elements):
    if t is None:
        continue

    key = key_from_texture(Path(t.texture).name)
    tree_img = ELEMENT_TEXTURES["trees"][key]

    tile_x = x / my_world.gen.config.TILE_SUBDIVISIONS
    tile_y = y / my_world.gen.config.TILE_SUBDIVISIONS

    i, j = camera.world_to_screen(tile_x, tile_y)

    t.set_coordinates(tile_x,tile_y)
    t.image = tree_img.copy()
    t.rect = tree_img.get_rect(midbottom=(i, j))

    tree_sprites.add(t)

# Main loop
import time
running_game = True
while running_game:
    frame_start = time.perf_counter()
    dt = clock.get_time() / 1000

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running_game = False
        elif event.type == pygame.KEYDOWN:
            if event.key == controls.OVERLAY_GRID_KEY:
                overlays.SHOW_GRID = not overlays.SHOW_GRID  # toggle grid visibility
            if event.key == pygame.K_KP_ENTER:
                my_world.generate()

    keys = pygame.key.get_pressed()

    camera.control(dt, keys=keys)

    if keys[pygame.K_q]:
        running_game = False

    screen.fill(BG_COLOR)

    # --- Find tiles inside the red rectangle ---
    rect_width, rect_height = cam_config.SCREEN_WIDTH, cam_config.SCREEN_HEIGHT
    rect_x = (window_size[0] - rect_width) // 2
    rect_y = (window_size[1] - rect_height) // 2
    red_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)


    tiles_in_rect = camera.get_tiles_in_rect(red_rect)
    print(f"Tiles in rect: {len(tiles_in_rect)}\n")


    # for y in range(my_world.tiles.shape[1]):
    #     for x in range(my_world.tiles.shape[0]):
    for (x,y) in tiles_in_rect:
        tile = my_world.get_tile(x,y)
        px, py = camera.world_to_screen(x, y)
        # py += tile.is_water * camera.tile_height_pxl // 2
        # px -= camera.tile_width_pxl // 2
        # py -= camera.tile_height_pxl // 2
        tile.rect.x = px
        tile.rect.y = py

        screen.blit(tile.image, (px, py))
        # Draw world coordinate text in the middle of the tile
        # coord_text = font.render(f"({x},{y})", True, (0,0,0))
        # text_rect = coord_text.get_rect(center=(px + camera.tile_width_pxl//2, py + camera.tile_height_pxl//2))
        # screen.blit(coord_text, text_rect)

    # tile_sprites.draw(screen)

    # for (y, x), obj in np.ndenumerate(my_world.elements):
    #     if obj is None:
    #         continue
    #     screen_x, screen_y = camera.world_to_screen(obj.x, obj.y)
    #     obj.rect.midbottom = (screen_x, screen_y)
    # tree_sprites.draw(screen)

    # ball_pos = camera.world_to_screen(5, 5)
    # pygame.draw.circle(screen, (255, 0, 0), ball_pos, 20)

    # camera.FPS counter
    fps_text = pygame.font.SysFont(None, 24).render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
    screen.blit(fps_text, (window_size[0] - 150, window_size[1] - 30))

    pygame.display.flip()
    clock.tick()

pygame.quit()
