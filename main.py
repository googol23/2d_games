import pygame
import random
import time
import heapq

import world
import character
import task
# -----------------------
# PATHFINDING UTILITIES
# -----------------------
def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

import heapq

def astar(world, start, goal, forbidden_terrains=None):
    """
    A* pathfinding from start to goal.
    forbidden_terrains: list of terrain types that cannot be crossed at all
    """
    neighbors = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)]
    close_set = set()
    came_from = {}
    gscore = {start:0}
    fscore = {start:abs(start[0]-goal[0]) + abs(start[1]-goal[1])}
    open_heap = []
    heapq.heappush(open_heap, (fscore[start], start))

    while open_heap:
        _, current = heapq.heappop(open_heap)

        if current == goal:
            # reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        close_set.add(current)

        for dx, dy in neighbors:
            neighbor = (current[0]+dx, current[1]+dy)
            nx, ny = neighbor

            if not (0 <= nx < world.world_size and 0 <= ny < world.world_size):
                continue

            terrain = world.tiles[ny][nx].terrain

            # Skip forbidden terrains completely
            if forbidden_terrains and terrain in forbidden_terrains:
                continue

            # Height / slope factor
            h_current = world.height_map[current[1]][current[0]]
            h_next = world.height_map[ny][nx]
            dh = h_next - h_current
            terrain_factor = 1 + 10*dh

            # Terrain cost multiplier
            terrain_factor = 1.0
            if "water" in terrain:
                terrain_factor = 10  # water is crossable, but high cost

            tentative_g_score = gscore[current] + terrain_factor

            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue

            if tentative_g_score < gscore.get(neighbor, float('inf')):
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + abs(nx-goal[0]) + abs(ny-goal[1])
                heapq.heappush(open_heap, (fscore[neighbor], neighbor))

    return []  # no path found


# -----------------------
# CHARACTER MOVEMENT
# -----------------------
def move_character(world, c, pos, path, delta_time):
    if not path:
        return pos, path

    x, y = pos
    target_tile = path[0]
    tx, ty = target_tile

    dx = tx - x
    dy = ty - y
    dist = (dx**2 + dy**2)**0.5
    if dist == 0:
        path.pop(0)
        return (x, y), path

    # Slope factor
    h_current = world.height_map[int(y)][int(x)]
    h_next = world.height_map[ty][tx]
    dh = h_next - h_current
    terrain_factor = 1 -10*dh

    # Terrain cost multiplier
    if "water" in world.tiles[int(y)][int(x)].terrain:
        terrain_factor = 0.2  # water is crossable, but high cost

    # Adjust speed
    adjusted_speed = c.speed * terrain_factor * (c.energy / 100)

    # Update character
    c.current_speed = adjusted_speed
    c.energy *= (1 - 0.01 * (1-min(0.95,terrain_factor))/ c.skills['Endurance'])

    move_dist = min(dist, adjusted_speed * delta_time)
    new_x = x + dx/dist * move_dist
    new_y = y + dy/dist * move_dist

    if (new_x - tx)**2 + (new_y - ty)**2 < 0.01:
        path.pop(0)

    return (new_x, new_y), path

# -----------------------
# INITIALIZATION
# -----------------------
my_world = world.World(100)
my_world.generate(
    terrain_weights={"water":1, "barren":0.5, "grassland":1, "forest":1, "mountain":1},
    water_level=0.1, mountain_level=0.7, n_of_peaks=100, seed=23
)

for i in range(1):
    h = character.Human(f"C{i}", age=20+i)
    my_world.add_character(h)

pygame.init()
screen_size = 800
screen = pygame.display.set_mode((screen_size, screen_size))
clock = pygame.time.Clock()
tile_size = screen_size // my_world.world_size
zoom_step = 0.1
running = True
font = pygame.font.SysFont(None, 20)

# Character state
char_positions = {c:(0,0) for c in my_world.characters}
char_paths = {c:[] for c in my_world.characters}
char_idle_timer = {c:0 for c in my_world.characters}
char_random_target = {c:None for c in my_world.characters}

# Selection
lasso_start = None
selected_chars = set()
directions = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)]

def current_time():
    return time.time()

# -----------------------
# LIVE PLOT SETUP
# -----------------------
import matplotlib
matplotlib.use("tkagg")  # or "qt5agg", "wxagg", "gtk3agg", depending on your system
import matplotlib.pyplot as plt

plt.ion()
fig, ax = plt.subplots(figsize=(6,3))
speed_line, = ax.plot([], [], label="Speed (tiles/sec)")
energy_line, = ax.plot([], [], label="Energy")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Value")
ax.set_title("Character Speed and Energy")
ax.legend()
plt.show(block=False)

log_data = {"time": [], "speed": [], "energy": []}
start_time = time.time()

# -----------------------
# MAIN LOOP
# -----------------------
task_mode = False
task_stage = None      # "root", "item", "location"
task_choice = {}       # {"action":..., "item":..., "location":...}

ROOT_KEYS = {
    pygame.K_g: "Gathering",
    pygame.K_b: "Building",
    pygame.K_h: "Hunting",
    pygame.K_c: "Crafting",
}

while running:
    # Time and delta
    now = current_time()
    delta_time = clock.tick(30) / 1000.0
    prev_positions = {c: char_positions[c] for c in my_world.characters}

    # -----------------------
    # Event handling
    # -----------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Start lasso selection
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            lasso_start = event.pos
            selected_chars.clear()

        # End lasso selection
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and lasso_start:
            x1, y1 = lasso_start
            x2, y2 = event.pos
            left, right = min(x1, x2) // tile_size, max(x1, x2) // tile_size
            top, bottom = min(y1, y2) // tile_size, max(y1, y2) // tile_size
            for c, (x, y) in char_positions.items():
                if left <= x <= right and top <= y <= bottom:
                    selected_chars.add(c)
            lasso_start = None

        # Right-click target assignment
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mx, my = event.pos
            target_tile = (mx // tile_size, my // tile_size)
            for c in selected_chars:
                char_paths[c] = astar(my_world, (int(char_positions[c][0]), int(char_positions[c][1])), target_tile)
                char_idle_timer[c] = now + 1
                c.idle = False

        # Zoom in/out
        elif event.type == pygame.MOUSEWHEEL:
            zoom += zoom_step if event.y > 0 else -zoom_step
            zoom = max(0.1, zoom)
            tile_size = int((screen_size / my_world.world_size) * zoom)

        elif event.type == pygame.KEYDOWN:
            # Enter task assignment mode
            if event.key == pygame.K_t:
                task_mode = True
                task_stage = "root"
                task_choice = {}
                print("Task assignment started.")

            elif task_mode:
                # 1. choose action
                if task_stage == "root" and event.key in ROOT_KEYS:
                    action = ROOT_KEYS[event.key]
                    task_choice["action"] = action
                    task_stage = "item"
                    print(f"Action: {action}")

                # 2. choose item
                elif task_stage == "item":
                    action = task_choice["action"]
                    if event.key in task.TASK_TREE[action]["keys"]:
                        item = task.TASK_TREE[action]["keys"][event.key]
                        task_choice["item"] = item
                        task_stage = "location"
                        print(f"Item: {item}")

                # 3. choose location
                elif task_stage == "location" and event.key in task.LOCATIONS["keys"]:
                    location_choice = task.LOCATIONS["keys"][event.key]
                    if location_choice == "here":
                        loc = (int(char_positions[c][0]), int(char_positions[c][1]))
                    elif location_choice == "mouse":
                        mx, my = pygame.mouse.get_pos()
                        loc = (mx//tile_size, my//tile_size)
                    task_choice["location"] = loc

                    # assign task to all selected characters
                    for c in selected_chars:
                        c.add_task({
                            "action" : action,
                            "item" : item,
                            "location" : loc,
                        })

                        print(f"Assigned: {task_choice}\nto Character: {c.name} ")
                    task_mode = False
                    task_stage = None

    # -----------------------
    # Update characters
    # -----------------------
    for c in my_world.characters:
        x, y = char_positions[c]

        # -----------------------
        # Perform task
        # -----------------------
        if c.tasks:
            task = c.tasks[0]  # look at first task in the queue
            action = task.get("action")
            item   = task.get("item")
            target = task.get("location")

            x, y = char_positions[c]

            # 1. Gathering tasks
            if action == "Gathering":
                if (int(x), int(y)) != target:
                    # not at drop location yet → pathfind there
                    if not char_paths[c]:
                        char_paths[c] = astar(my_world, (int(x), int(y)), target)
                else:
                    # at drop location → simulate gathering loop
                    if random.random() < 0.05:  # 1% chance per frame to "find item"
                        print(f"{c.name} found {item} and dropped it at {target}.")
                        c.inventory[item] = c.inventory.get(item, 0) + 1
                    else:
                        dx = random.randint(-2, 2)
                        dy = random.randint(-2, 2)

                        # compute target tile
                        nx = max(0, min(my_world.world_size-1, x + dx))
                        ny = max(0, min(my_world.world_size-1, y + dy))

                        # compute path
                        char_paths[c] = astar(my_world, (int(x), int(y)), (nx, ny))

            # 2. Building tasks
            elif action == "build":
                if (int(x), int(y)) != target:
                    if not char_paths[c]:
                        char_paths[c] = astar(my_world, (int(x), int(y)), target)
                else:
                    # arrived at location → build
                    print(f"{c.name} is building {item} at {target}.")
                    # fake progress
                    task.setdefault("progress", 0)
                    task["progress"] += 1
                    if task["progress"] > 50:  # done after 50 ticks
                        print(f"{item} built at {target}.")
                        c.tasks.pop(0)  # task complete

                # Extend with more actions as needed...

        if char_paths[c]:
            # Follow assigned path
            new_pos, char_paths[c] = move_character(my_world, c, (x, y), char_paths[c], delta_time)
            char_positions[c] = new_pos
            c.idle = False
            char_idle_timer[c] = now + 1

    # -----------------------
    # Rendering
    # -----------------------
    screen.fill((0, 0, 0))
    my_world.render_world(screen)

    # Draw characters, paths, speed & energy
    for c, (x, y) in char_positions.items():
        color = (0, 255, 0) if c in selected_chars else (255, 0, 0)
        pygame.draw.circle(screen, color, (int(x*tile_size + tile_size/2), int(y*tile_size + tile_size/2)), max(2, tile_size//2))

        # Path
        path = char_paths[c]
        if path and len(path) > 1:
            points = [(px*tile_size + tile_size/2, py*tile_size + tile_size/2) for px, py in path]
            pygame.draw.lines(screen, (0, 255, 255), False, points, max(1, int(tile_size/8)))

        # Selected character stats and live plot
        if c in selected_chars:
            log_data["time"].append(now)
            log_data["speed"].append(c.current_speed)
            log_data["energy"].append(c.energy)
            if len(log_data["time"]) % 3 == 0:
                speed_line.set_data(log_data["time"], log_data["speed"])
                energy_line.set_data(log_data["time"], log_data["energy"])
                ax.relim()
                ax.autoscale_view()
                plt.pause(0.001)
            text_surface = font.render(f"{c.current_speed:.2f} t/s | {c.energy:.1f} E", True, (255,0,0))
            screen.blit(text_surface, (x*tile_size, y*tile_size - 10))

    # -----------------------
    # Fog of War
    # -----------------------
    fog = pygame.Surface((screen_size, screen_size), flags=pygame.SRCALPHA)  # enable per-pixel alpha
    fog.fill((0, 0, 0, 200))  # semi-transparent black
    fog.set_alpha(200)
    for c, (x, y) in char_positions.items():
        cx, cy = int(x*tile_size + tile_size/2), int(y*tile_size + tile_size/2)
        visibility_radius = 10
        radius_px = int(visibility_radius * tile_size)
        pygame.draw.circle(fog, (0,0,0,0), (cx, cy), radius_px)
    screen.blit(fog, (0, 0))

    # Draw lasso selection rectangle
    if lasso_start:
        mx, my = pygame.mouse.get_pos()
        rect = pygame.Rect(min(lasso_start[0], mx), min(lasso_start[1], my),
                           abs(mx - lasso_start[0]), abs(my - lasso_start[1]))
        pygame.draw.rect(screen, (0, 255, 0), rect, 2)

    pygame.display.flip()

pygame.quit()
plt.ioff()
plt.show()