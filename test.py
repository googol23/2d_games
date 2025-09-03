import pygame
import sys
import matplotlib.cm as cm
import numpy as np
from world import generate_topological_map
from world import find_path  # your optimized pathfinding

# --- Configuration ---
TILE_SIZE = 10  # base tile size in pixels
FPS = 60
SPEED = 5  # tiles/sec

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 1000  # display resolution

# --- Generate topo map ---
topo = generate_topological_map(100, 100, 10, 23)
rows, cols = topo.shape

# --- Normalize topo map for colormap ---
norm_topo = (topo - np.min(topo)) / (np.max(topo) - np.min(topo))
cmap = cm.get_cmap("terrain")

def topo_to_color(y, x):
    r, g, b, _ = cmap(norm_topo[y, x])
    return int(r*255), int(g*255), int(b*255)

# --- Pygame init ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# --- Dot state ---
dot_pos = [0.5, 0.5]
waypoints = [dot_pos[:]]
target_index = 1

# --- Camera ---
CAM_WIDTH, CAM_HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT

def get_camera_offset():
    # Center camera on dot
    cam_x = int(dot_pos[0]*TILE_SIZE - CAM_WIDTH//2)
    cam_y = int(dot_pos[1]*TILE_SIZE - CAM_HEIGHT//2)
    # Clamp so we don't see beyond map edges
    cam_x = max(0, min(cam_x, cols*TILE_SIZE - CAM_WIDTH))
    cam_y = max(0, min(cam_y, rows*TILE_SIZE - CAM_HEIGHT))
    return cam_x, cam_y

def draw_world():
    cam_x, cam_y = get_camera_offset()
    for y in range(rows):
        for x in range(cols):
            color = topo_to_color(y, x)
            rect = pygame.Rect(x*TILE_SIZE - cam_x, y*TILE_SIZE - cam_y, TILE_SIZE, TILE_SIZE)
            # Only draw if visible
            if rect.right >= 0 and rect.left <= SCREEN_WIDTH and rect.bottom >=0 and rect.top <= SCREEN_HEIGHT:
                pygame.draw.rect(screen, color, rect)

def move_dot(dt):
    global target_index
    if target_index >= len(waypoints):
        return
    tx, ty = waypoints[target_index]
    dx = tx - dot_pos[0]
    dy = ty - dot_pos[1]
    dist = (dx**2 + dy**2)**0.5
    if dist < 1e-4:
        target_index += 1
        return
    step = SPEED * dt
    if step >= dist:
        dot_pos[0] = tx
        dot_pos[1] = ty
        target_index += 1
    else:
        dot_pos[0] += dx / dist * step
        dot_pos[1] += dy / dist * step

# --- Main loop ---
while True:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mouse_x, mouse_y = event.pos
            cam_x, cam_y = get_camera_offset()
            # Convert mouse to world coords
            target_x = (mouse_x + cam_x) / TILE_SIZE
            target_y = (mouse_y + cam_y) / TILE_SIZE
            new_path = find_path(dot_pos[0], dot_pos[1], target_x, target_y, topo)
            if new_path:
                waypoints = new_path
                target_index = 1

    move_dot(dt)

    screen.fill((0,0,0))
    draw_world()

    # Draw path for visualization
    cam_x, cam_y = get_camera_offset()
    for wp in waypoints[target_index:]:
        px, py = int(wp[0]*TILE_SIZE - cam_x), int(wp[1]*TILE_SIZE - cam_y)
        pygame.draw.circle(screen, (0,255,0), (px, py), 3)

    # Draw red dot
    px, py = int(dot_pos[0]*TILE_SIZE - cam_x), int(dot_pos[1]*TILE_SIZE - cam_y)
    pygame.draw.circle(screen, (255,0,0), (px, py), max(2, TILE_SIZE//3))

    pygame.display.flip()
