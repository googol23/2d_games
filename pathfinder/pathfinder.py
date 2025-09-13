import numpy as np
import math
import heapq
from world import World
from agent import Agent

# ------------------- Movement Cost -------------------
def movement_cost(from_x: int, from_y: int, to_x: int, to_y: int,
                  height_map: np.ndarray, agent: Agent) -> float:
    """
    Compute movement cost from one tile to another.
    Includes:
        - Euclidean distance (base cost)
        - Uphill penalty (10 per unit height gain)
        - Terrain penalty (slower tiles increase cost)
    """
    base = math.hypot(to_x - from_x, to_y - from_y)
    height_diff = height_map[to_y, to_x] - height_map[from_y, from_x]
    height_penalty = max(0.0, 10 * height_diff)
    terrain_penalty = agent.base_speed / agent.speed_at(to_x, to_y)
    return base + height_penalty + terrain_penalty

# ------------------- Heuristic -------------------
def heuristic(x1: int, y1: int, x2: int, y2: int) -> float:
    """Euclidean distance heuristic for A*."""
    return math.hypot(x2 - x1, y2 - y1)

# ------------------- A* Search -------------------
def astar_find_path(start_x: int, start_y: int, goal_x: int, goal_y: int,
                    width: int, height: int,
                    height_map: np.ndarray,
                    obstacle_map: np.ndarray,
                    agent: Agent) -> list[tuple[int, int]] | None:
    """
    A* search for pathfinding on a grid.
    Returns list of (x, y) tiles from start to goal, or None if unreachable.
    """
    # Priority queue: (f_score, x, y, g_score)
    open_list = []
    heapq.heappush(open_list, (heuristic(start_x, start_y, goal_x, goal_y),
                               start_x, start_y, 0.0))
    
    # Maps to track path and costs
    parent_map = -np.ones((height, width), dtype=np.int64)
    g_map = np.full((height, width), np.inf, dtype=np.float64)
    g_map[start_y, start_x] = 0.0

    # 8 possible movement directions
    dirs = [(-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0), (1, 1)]

    while open_list:
        f_curr, x_curr, y_curr, g_curr = heapq.heappop(open_list)

        # Goal reached: reconstruct path
        if x_curr == goal_x and y_curr == goal_y:
            path = []
            idx = y_curr * width + x_curr
            while idx >= 0:
                y = idx // width
                x = idx % width
                path.append((x, y))
                idx = parent_map[y, x]
            return path[::-1]  # reverse path

        # Explore neighbors
        for dx, dy in dirs:
            nx, ny = x_curr + dx, y_curr + dy
            if 0 <= nx < width and 0 <= ny < height:
                if obstacle_map[ny, nx]:
                    continue

                # Prevent diagonal corner cutting
                if dx != 0 and dy != 0:
                    if obstacle_map[y_curr, nx] and obstacle_map[ny, x_curr]:
                        continue

                tentative_g = g_curr + movement_cost(x_curr, y_curr, nx, ny, height_map, agent)
                if tentative_g < g_map[ny, nx]:
                    g_map[ny, nx] = tentative_g
                    f_new = tentative_g + heuristic(nx, ny, goal_x, goal_y)
                    heapq.heappush(open_list, (f_new, nx, ny, tentative_g))
                    parent_map[ny, nx] = y_curr * width + x_curr

    # Path not found
    return None

# ------------------- Pathfinder Wrapper -------------------
class Pathfinder:
    """Wrapper for A* pathfinding in a World."""
    
    def __init__(self, world: World):
        self.world = world
        # Convert height and obstacle maps to NumPy arrays
        self.height_map = np.array(world.height_map, dtype=np.float64)
        self.obstacle_map = np.array(world.obstacle_map, dtype=np.bool_)
        self.width = world.world_size_x
        self.height = world.world_size_y

    def find_path(self, start: tuple[float, float], goal: tuple[float, float], agent: Agent) -> list[tuple[float, float]] | None:
        """
        Find path from start to goal for a given agent.
        Returns list of float positions (tile centers).
        """
        start_tile = int(start[0]), int(start[1])
        goal_tile = int(goal[0]), int(goal[1])

        path_tiles = astar_find_path(start_tile[0], start_tile[1],
                                     goal_tile[0], goal_tile[1],
                                     self.width, self.height,
                                     self.height_map,
                                     self.obstacle_map,
                                     agent)
        if path_tiles is None:
            return None

        # Convert tile path to float positions at tile centers
        path = [(x + 0.5, y + 0.5) for x, y in path_tiles]
        path[0] = start
        path[-1] = goal
        return path
