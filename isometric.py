import controls
import overlays
from world import World, WorldGen, WorldGenConfig
import pygame, random, os
from pathlib import Path

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

# Parameters
FPS = 120
TILE_WIDTH = 128
TILE_HEIGHT = 64
TILE_SCALE = 0.5 # Tiles per meter
GRID_WIDTH  = 50
GRID_HEIGHT = 50
BG_COLOR = (30, 30, 30)
OFFSET_X = 1
OFFSET_Y = 0
RIVER_OFFSET_Y = TILE_HEIGHT // 2

# Initialize pygame
pygame.init()
window_size = (1600, 1000)
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
            img = pygame.transform.scale(img, (TILE_WIDTH, TILE_HEIGHT * 2))
            img.set_colorkey((0, 0, 0))
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
            img = pygame.transform.scale(img, (2*TILE_HEIGHT,2*TILE_HEIGHT))
            ELEMENT_TEXTURES[element][key] = img


# World configuration
# --- Initialize world ---
world_config = WorldGenConfig(  SIZE_X= GRID_WIDTH,
                                SIZE_Y= GRID_HEIGHT,
                                SCALE = 10,
                                TILE_SUBDIVISIONS=1,
                                WATER_RATIO=0.15,
                                MOUNTAIN_RATIO=0.15,
                                ICE_CAP_RATIO=0.01
                              )
world_gentor = WorldGen(config=world_config)
my_world = World(world_gentor)
my_world.generate()
print(my_world)


# Directory containing tile images
character_dir = "./textures/agents/male_human/animations/"

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

        self.walk_speed = 0.4*TILE_SCALE / FPS  # tiles per frame
        self.run_speed  = 1.6*TILE_SCALE / FPS  # tiles per frame

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

    def update(self, keys):
        moving = False
        speed = self.walk_speed

        # Running vs walking
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and (keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]):
            self.current_animations = self.running_animations
            speed = self.run_speed
        else:
            self.current_animations = self.walking_animations
            speed = self.walk_speed

        # Movement in fractional tile units
        if keys[pygame.K_w]:
            self.y -= speed
            self.direction = 'north'
            moving = True
        if keys[pygame.K_s]:
            self.y += speed
            self.direction = 'south'
            moving = True
        if keys[pygame.K_a]:
            self.x -= speed
            self.direction = 'west'
            moving = True
        if keys[pygame.K_d]:
            self.x += speed
            self.direction = 'east'
            moving = True

        # Update animation frame
        if moving:
            self.frame_counter += 1
            if self.frame_counter >= self.frame_delay:
                self.frame_index = (self.frame_index + 1) % len(self.current_animations[self.direction])
                self.frame_counter = 0
        else:
            self.frame_index = 0

    def draw(self, surface, camera_x, camera_y):
        # Convert world coordinates to pixel coordinates
        px = int(self.x * TILE_WIDTH)
        py = int(self.y * TILE_HEIGHT)
        img = self.current_animations[self.direction][self.frame_index]
        surface.blit(img, (px + camera_x - img.get_width()//2, py + camera_y - img.get_height()))

# --- Initialize character ---
char_start_pos = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
character = Human(character_dir, start_pos=char_start_pos,frame_delay=FPS/8)


# Function to convert grid coords to isometric pixel coords
def world_to_iso(x:float, y:float) -> tuple[int,int]:
    return int((x - y) * (TILE_WIDTH // 2)), int((x + y) * (TILE_HEIGHT // 2))


# Create world surface
center_x = int((GRID_WIDTH + GRID_HEIGHT) * (TILE_WIDTH // 4) - TILE_WIDTH // 2 + OFFSET_X)
world_width = (GRID_WIDTH + GRID_HEIGHT) * (TILE_WIDTH // 2)
world_height = (GRID_WIDTH + GRID_HEIGHT) * (TILE_HEIGHT // 2) + TILE_HEIGHT * 2
world_surface = pygame.Surface((world_width, world_height), pygame.SRCALPHA)

tile_hight_map = my_world.gen.tile_heights_map
sorted_z = []
for s in range(my_world.size_x + my_world.size_y - 1):  # sum of indices
    for y in range(my_world.size_y):
        x = s - y
        if 0 <= x < my_world.size_x:
            sorted_z.append((x,y))

for col,row in sorted_z:
    current_tile = my_world.get_tile(col, row)
    x, y = world_to_iso(col, row)
    pos_y = y + OFFSET_Y

    # Select a tile image from the correct terrain
    terrain_name = current_tile.terrain.name
    tile_imgs = TILE_TEXTURES.get(terrain_name)
    if not tile_imgs:
        raise RuntimeError(f"No textures loaded for terrain '{terrain_name}'")
    img = random.choice(tile_imgs)  # <-- use a random tile image for variety

    # Apply water offset if needed
    if current_tile.is_water:
        offset_y = TILE_HEIGHT // 2
    elif current_tile.terrain.name in ["mountain", "ice_cap"]:
        offset_y = 0#-round(TILE_HEIGHT * tile_hight_map[row,col])
    else:
        offset_y = 0

    # Blit tile to world surface
    world_surface.blit(img, (int(x + center_x), int(y + offset_y)))

# --- Create a cached grid surface ---
# Pre-render the grid once
grid_surface = overlays.draw_grid(
    GRID_WIDTH, GRID_HEIGHT, TILE_WIDTH, TILE_HEIGHT,
    offset_x=center_x + TILE_WIDTH//2,
    offset_y=OFFSET_Y,
    color=(0, 0, 0, 100),
    grid_to_iso=world_to_iso
)
world_with_grid_surface = world_surface.copy()
world_with_grid_surface.blit(grid_surface, (0, 0))

# Add trees
world_elements = pygame.sprite.LayeredUpdates()
def generate_trees_surface(world:World, trees_dict:dict[tuple[int,int],pygame.Surface], tile_w, tile_h, center_x=0, offset_y=0):
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

            iso_x, iso_y = world_to_iso(tile_x, tile_y)
            tile_center_x = iso_x + center_x + tile_w // 2
            tile_center_y = iso_y + offset_y + tile_h // 2

            pos_x = tile_center_x - tree_img.get_width() // 2
            pos_y = tile_center_y - tree_img.get_height()
            surface.blit(tree_img, (pos_x, pos_y))

    return surface


tree_surface = generate_trees_surface(
    my_world,
    trees_dict=ELEMENT_TEXTURES["trees"],
    tile_w=TILE_WIDTH,
    tile_h=TILE_HEIGHT,
    center_x=center_x,
    offset_y=OFFSET_Y
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
camera_x, camera_y = GRID_WIDTH//2, GRID_HEIGHT//2
camera_speed = 8
font = pygame.font.SysFont(None, 24)

# Main loop
running_game = True
while running_game:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running_game = False
        elif event.type == pygame.KEYDOWN:
            if event.key == controls.OVERLAY_GRID_KEY:
                overlays.SHOW_GRID = not overlays.SHOW_GRID  # toggle grid visibility

    keys = pygame.key.get_pressed()

    # Camera movement
    if keys[pygame.K_LEFT]: camera_x += 8
    if keys[pygame.K_RIGHT]: camera_x -= 8
    if keys[pygame.K_UP]: camera_y += 8
    if keys[pygame.K_DOWN]: camera_y -= 8

    # Update character
    character.update(keys)


    world_elements.update()
    # world_elements.draw(tree_surface)

    screen.fill(BG_COLOR)

    if overlays.SHOW_GRID:
        screen.blit(world_with_grid_surface, (int(camera_x), int(camera_y)))
    else:
        screen.blit(world_surface, (int(camera_x), int(camera_y)))


    character.draw(screen, camera_x, camera_y)
    screen.blit(tree_surface, (camera_x, camera_y))


    # FPS counter
    fps_text = pygame.font.SysFont(None, 24).render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
    screen.blit(fps_text, (window_size[0] - 90, window_size[1] - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
