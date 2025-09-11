import numpy as np
import heapq
import math
from numba import njit, prange
from world import World

# ------------------- Optimized movement cost -------------------
@njit(inline="always")
def movement_cost(from_x: int, from_y: int, to_x: int, to_y: int, height_map: np.ndarray) -> float:
    """Calculate movement cost with height penalty (uphill only)."""
    base = math.hypot(to_x - from_x, to_y - from_y)
    height_diff = height_map[to_y, to_x] - height_map[from_y, from_x]
    penalty = max(0.0, 10*height_diff)
    return base + penalty

@njit(inline="always")
def heuristic(x1: int, y1: int, x2: int, y2: int) -> float:
    """Euclidean heuristic."""
    return math.hypot(x2 - x1, y2 - y1)

from numba import njit
import numpy as np
import math

@njit
def astar_find_path(start_x: int, start_y: int, goal_x: int, goal_y: int,
                    width: int, height: int,
                    height_map: np.ndarray, obstacle_map: np.ndarray) -> list[tuple[int, int]] | None:
    """
    Numba-compatible A* search.
    Prevents diagonal corner cutting (can't slip through two blocked neighbors).
    Returns path as list of (x, y) tiles or None if not found.
    """
    open_list = [(math.hypot(goal_x - start_x, goal_y - start_y), start_x, start_y, 0.0)]
    parent_map = -np.ones((height, width), dtype=np.int64)
    g_map = np.full((height, width), np.inf, dtype=np.float64)
    g_map[start_y, start_x] = 0.0

    dirs = np.array([(-1, -1), (-1, 0), (-1, 1),
                     (0, -1),          (0, 1),
                     (1, -1),  (1, 0), (1, 1)], dtype=np.int64)

    while len(open_list) > 0:
        # sort open list by f-cost
        open_list.sort(key=lambda n: n[0])
        f_curr, x_curr, y_curr, g_curr = open_list.pop(0)

        if x_curr == goal_x and y_curr == goal_y:
            # reconstruct path
            path = []
            idx = y_curr * width + x_curr
            while idx >= 0:
                y = idx // width
                x = idx % width
                path.append((x, y))
                idx = parent_map[y, x]
            return path[::-1]

        for dx, dy in dirs:
            nx, ny = x_curr + dx, y_curr + dy
            if 0 <= nx < width and 0 <= ny < height:
                if obstacle_map[ny, nx]:
                    continue

                # --- Prevent diagonal corner cutting ---
                if dx != 0 and dy != 0:  # diagonal move
                    if obstacle_map[y_curr, nx] and obstacle_map[ny, x_curr]:
                        continue

                # tentative_g = g_curr + math.hypot(dx, dy) + max(0.0, height_map[ny, nx] - height_map[y_curr, x_curr])
                tentative_g = movement_cost(start_x,start_y,goal_x,goal_y,height_map)
                if tentative_g < g_map[ny, nx]:
                    g_map[ny, nx] = tentative_g
                    f_new = tentative_g + math.hypot(goal_x - nx, goal_y - ny)
                    open_list.append((f_new, nx, ny, tentative_g))
                    parent_map[ny, nx] = y_curr * width + x_curr

    return None


class Pathfinder:
    """Python wrapper around optimized Numba A*."""

    def __init__(self, world:World):
        self.world = world
        # Convert height_map and obstacle_map to numpy arrays
        self.height_map = np.array(world.height_map, dtype=np.float64)
        self.obstacle_map = np.array(world.obstacle_map, dtype=np.bool)
        self.width = world.world_size_x
        self.height = world.world_size_y

    def find_path(self, start: tuple[float, float], goal: tuple[float, float]) -> list[tuple[float, float]] | None:
        start_tile = int(start[0]), int(start[1])
        goal_tile = int(goal[0]), int(goal[1])
        path_tiles = astar_find_path(start_tile[0], start_tile[1],
                                     goal_tile[0], goal_tile[1],
                                     self.width, self.height,
                                     self.height_map, self.obstacle_map)
        if path_tiles is None:
            return None

        # Convert tile path to float positions with center-of-tile
        path = [(x+0.5, y+0.5) for x, y in path_tiles]
        # Replace endpoints with exact start/end positions
        path[0] = start
        path[-1] = goal
        return path
