import controls
import overlays
from world import World, WorldGen, WorldGenConfig
import pygame, random, os


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

# World configuration
# --- Initialize world ---
world_config = WorldGenConfig(  SIZE_X= 50,
                                SIZE_Y= 50,
                                SCALE = 10,
                                TILE_SUBDIVISIONS=2,
                                WATER_RATIO=0.15,
                                MOUNTAIN_RATIO=0.15,
                                ICE_CAP_RATIO=0.01
                              )
world_gentor = WorldGen(config=world_config)
my_world = World(world_gentor)
my_world.generate()
print(my_world)


# Directory containing tile images
grass_dir = "./textures/terrains/grassland"
river_dir = "./textures/terrains/river"
trees_dir = "./textures/trees/"
character_dir = "./textures/agents/male_human/animations/"

# Initialize pygame
pygame.init()
window_size = (1600, 1000)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Isometric World with River Tile and Human")
clock = pygame.time.Clock()

# Load tiles textures
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
            img = pygame.transform.smoothscale(img, (TILE_WIDTH, TILE_HEIGHT * 2))
            img.set_colorkey((0, 0, 0))
            TILE_TEXTURES[terrain].append(img)
    if not TILE_TEXTURES[terrain]:
        raise RuntimeError(f"No PNG tiles found in {terrain_dir}")

trees = {}
for filename in os.listdir(trees_dir):
    if filename.lower().endswith(".png"):
        name, _ = os.path.splitext(filename)
        try:
            model, lifecycle = map(int, name.split("."))
        except ValueError:
            # skip files that don't match "N.M.png"
            continue
        path = os.path.join(trees_dir, filename)
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (2*TILE_HEIGHT,2*TILE_HEIGHT))
        trees[(model, lifecycle)] = img


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
def grid_to_iso(x, y):
    return int((x - y) * (TILE_WIDTH // 2)), int((x + y) * (TILE_HEIGHT // 2))


# Create world surface
center_x = int((GRID_WIDTH + GRID_HEIGHT) * (TILE_WIDTH // 4) - TILE_WIDTH // 2 + OFFSET_X)
world_width = (GRID_WIDTH + GRID_HEIGHT) * (TILE_WIDTH // 2)
world_height = (GRID_WIDTH + GRID_HEIGHT) * (TILE_HEIGHT // 2) + TILE_HEIGHT * 2
world_surface = pygame.Surface((world_width, world_height), pygame.SRCALPHA)

tile_hight_map = my_world.gen.tile_heights_map
for row in range(my_world.size_y):
    for col in range(my_world.size_x):
        current_tile = my_world.get_tile(col, row)
        x, y = grid_to_iso(col, row)
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
            offset_y = -round(TILE_HEIGHT * tile_hight_map[row,col])
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
    grid_to_iso=grid_to_iso
)
world_with_grid_surface = world_surface.copy()
world_with_grid_surface.blit(grid_surface, (0, 0))

# Add trees
world_elements = pygame.sprite.LayeredUpdates()
def generate_trees_surface(world:World, trees_dict, tile_w, tile_h, center_x=0, offset_y=0):
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

            # Pick a tree image that matches cycle 2 (or whatever you want)
            tree_keys = [k for k in trees_dict if k[1] == 2]
            if not tree_keys:
                continue
            key = random.choice(tree_keys)
            tree_img = trees_dict[key]

            # Compute tile coordinates
            tile_x = col // N
            tile_y = row // N

            iso_x, iso_y = grid_to_iso(tile_x, tile_y)
            tile_center_x = iso_x + center_x + tile_w // 2
            tile_center_y = iso_y + offset_y + tile_h // 2

            pos_x = tile_center_x - tree_img.get_width() // 2
            pos_y = tile_center_y - tree_img.get_height()
            surface.blit(tree_img, (pos_x, pos_y))

    return surface


tree_surface = generate_trees_surface(
    my_world,
    trees_dict=trees,
    tile_w=TILE_WIDTH,
    tile_h=TILE_HEIGHT,
    center_x=center_x,
    offset_y=OFFSET_Y
)



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

    screen.fill(BG_COLOR)

    if overlays.SHOW_GRID:
        screen.blit(world_with_grid_surface, (int(camera_x), int(camera_y)))
    else:
        screen.blit(world_surface, (int(camera_x), int(camera_y)))


    screen.blit(tree_surface, (camera_x, camera_y))

    character.draw(screen, camera_x, camera_y)

    # FPS counter
    fps_text = pygame.font.SysFont(None, 24).render(f"FPS: {int(clock.get_fps())}", True, (255, 255, 255))
    screen.blit(fps_text, (window_size[0] - 90, window_size[1] - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
