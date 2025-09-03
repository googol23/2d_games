import numpy as np
import heapq
import math
from numba import njit

@njit
def heuristic(a, b):
    return np.hypot(a[0] - b[0], a[1] - b[1])

@njit
def neighbors(y, x, h, w):
    # Note: y=row, x=col, h=rows, w=cols
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                yield ny, nx

@njit
def bresenham_line(y0, x0, y1, x1):
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        points.append((y0, x0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return points

@njit
def line_of_sight(grid, p1, p2):
    y0, x0 = p1
    y1, x1 = p2
    line = bresenham_line(y0, x0, y1, x1)
    for (y, x) in line:
        if grid[y, x] >= 1:
            return False
    return True

@njit
def compute_cost(grid, current, neighbor):
    y0, x0 = current
    y1, x1 = neighbor
    dz = grid[y1, x1] - grid[y0, x0]
    distance = np.hypot(x1 - x0, y1 - y0)
    slope_factor = 1 + 10*dz
    return distance * slope_factor

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]

def smooth_path(grid, path):
    if not path:
        return []
    waypoints = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and line_of_sight(grid, path[i], path[j]):
            j -= 1
        waypoints.append(path[j])
        i = j
    return [(x + 0.5, y + 0.5) for y, x in waypoints]

def find_path(x0, y0, x1, y1, topo_grid):
    h, w = topo_grid.shape  # rows, cols
    start = (int(y0), int(x0))
    goal  = (int(y1), int(x1))

    open_set = [(0, start)]
    came_from = {}
    g_score = np.full((h, w), np.inf)
    f_score = np.full((h, w), np.inf)
    g_score[start] = 0
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            tile_path = reconstruct_path(came_from, current)
            return smooth_path(topo_grid, tile_path)

        for ny, nx in neighbors(current[0], current[1], h, w):
            if topo_grid[ny, nx] >= 1:
                continue
            tentative_g = g_score[current] + compute_cost(topo_grid, current, (ny, nx))
            if tentative_g < g_score[ny, nx]:
                came_from[(ny, nx)] = current
                g_score[ny, nx] = tentative_g
                f_score[ny, nx] = tentative_g + heuristic((ny, nx), goal)
                heapq.heappush(open_set, (f_score[ny, nx], (ny, nx)))
    return []
