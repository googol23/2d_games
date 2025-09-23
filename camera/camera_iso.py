import pygame
from functools import cached_property
import math
import numpy as np

from world import World

import logging
logger = logging.getLogger("camera_iso")

class CameraIsoConfig:
    def __init__(
        self,
        fps:int = 60,
        speed_tiles: float = 0.1, # TILES per frame
        zoom_step: int = 24,
        pan_edge_size: int = 10,
        min_tile_size: int = 64,
        max_tile_size: int = 256,
        screen_with: int = 800,
        screen_height: int = 600,
        tile_width: int = 256,
        tile_height: int = 128,
    ):
        self.SPEED_TILES = speed_tiles      # Percent of visible tiles per move
        self.ZOOM_STEP = zoom_step
        self.MIN_TILE_SIZE = min_tile_size
        self.MAX_TILE_SIZE = max_tile_size
        self.PAN_EDGE_SIZE = pan_edge_size
        self.SCREEN_WIDTH = screen_with
        self.SCREEN_HEIGHT = screen_height
        self.TILE_WIDTH = tile_width
        self.TILE_HEIGHT = tile_height
        self.FPS = fps


class CameraIso:
    def __init__(self,
                 world: World | None = None,
                 start_x: float = 0,
                 start_y: float = 0,
                 config: CameraIsoConfig = CameraIsoConfig()):
        self.world = world
        self.x = start_x  # world coordinates (tiles, float)
        self.y = start_y  # world coordinates (tiles, float)
        self.config = config

    @cached_property
    def iso_offset_x(self) -> int:
        return self.screen_width // 2

    @cached_property
    def iso_offset_y(self) -> int:
        return 0

    @cached_property
    def tile_width_pxl(self) -> int:
        """ Tile width in pixels. """
        return self.config.TILE_WIDTH

    @cached_property
    def tile_height_pxl(self) -> int:
        """ Tile height in pixels. """
        return self.config.TILE_HEIGHT

    @cached_property
    def screen_width(self) -> int:
        """ Screen width in pixels. """
        return self.config.SCREEN_WIDTH

    @cached_property
    def screen_height(self) -> int:
        """ Screen height in pixels. """
        return self.config.SCREEN_HEIGHT

    @cached_property
    def world_width_pxl(self) -> int:
        """ World width in pixels. """
        if self.world is None:
            return 0
        return (self.world.size_x + self.world.size_y) * self.tile_width_pxl // 2

    @cached_property
    def world_height_pxl(self) -> int:
        """ World width in pixels. """
        if self.world is None:
            return 0
        return (self.world.size_x + self.world.size_y) * self.tile_height_pxl // 2

    @cached_property
    def FPS(self) -> int:
        """ Frames per second. """
        return self.config.FPS


    def _invalidate_cache(self):
        """Invalidate cached properties."""
        for attr in ['tile_width_pxl', 'tile_height_pxl', 'screen_width', 'screen_height']:
            if attr in self.__dict__:
                del self.__dict__[attr]

    # ---- Camera operations ----
    def move(self, dx: float, dy: float):
        """Move the camera in world coordinates (tiles)."""
        self.x += dx
        self.y += dy

    @cached_property
    def speed_x_pxl(self) -> int:
        return self.config.SPEED_TILES * self.config.TILE_WIDTH
    @cached_property
    def speed_y_pxl(self) -> int:
        return self.config.SPEED_TILES * self.config.TILE_HEIGHT

    def control(self, dt:float, keys=None, events=None, mouse_pos=None):
        dx, dy = 0.0, 0.0
        # Screen-based camera panning
        if keys[pygame.K_UP]:
            dy += 1
        if keys[pygame.K_DOWN]:
            dy -= 1
        if keys[pygame.K_LEFT]:
            dx += 1
        if keys[pygame.K_RIGHT]:
            dx -= 1

        # normalize if moving
        if dx != 0 or dy != 0:
            length = math.sqrt(dx*dx + dy*dy)
            dx /= length
            dy /= length
            self.x += dx * self.speed_x_pxl * dt
            self.y += dy * self.speed_y_pxl * dt

    # --- Coordinate transformations ---
    @cached_property
    def w2s_matrix(self) -> np.ndarray:
        return np.array([
            [+self.config.TILE_WIDTH / 2, +self.config.TILE_HEIGHT / 2],
            [-self.config.TILE_WIDTH / 2, +self.config.TILE_HEIGHT / 2]
        ])

    @cached_property
    def s2w_matrix(self) -> np.ndarray:
        return np.linalg.inv(self.w2s_matrix)

    @cached_property
    def screen_offset(self) -> np.ndarray:
        return np.array([self.config.SCREEN_WIDTH / 2, self.config.SCREEN_HEIGHT / 4])

    def world_to_screen(self, x, y):
        """
        Transforms world coordinates (x, y) to screen coordinates.
        This includes the camera's current offset.
        x and y can be scalars or NumPy arrays.
        """
        world_coords = np.stack([x, y], axis=-1)
        # Apply isometric projection, add screen offset, and then apply camera view offset
        screen_coords = world_coords @ self.w2s_matrix + self.screen_offset + np.array([self.x, self.y])
        return screen_coords.astype(int)


    def screen_to_world(self, screen_x, screen_y):
        """
        Transforms screen coordinates (screen_x, screen_y) to world coordinates.
        screen_x and screen_y can be scalars or NumPy arrays.
        """
        screen_coords = np.stack([screen_x, screen_y], axis=-1)
        # Reverse the transformation: (screen - camera - offset) @ inv_matrix
        world_coords = (screen_coords - np.array([self.x, self.y]) - self.screen_offset) @ self.s2w_matrix
        return world_coords.astype(int)

    def get_tiles_in_rect(self, selection_rect):
        """
        Calculates the set of world grid tiles that intersect with a given screen rectangle.

        This is an optimized function that first converts the screen rectangle's corners
        to world coordinates to define a smaller search area, rather than iterating over
        the entire world grid.
        Args:
            selection_rect (pygame.Rect): The rectangle on the screen.

        Returns:
            set[tuple[int, int]]: A set of (x, y) world coordinates for the intersecting tiles.
        """
        # 1. Convert screen rect corners to world coordinates to define a search area.
        # The screen_to_world method now handles the camera offset, so we don't subtract it here.
        rect_corners_screen_x = np.array([selection_rect.left, selection_rect.right, selection_rect.right, selection_rect.left])
        rect_corners_screen_y = np.array([selection_rect.top, selection_rect.top, selection_rect.bottom, selection_rect.bottom])
        world_corners = self.screen_to_world(rect_corners_screen_x, rect_corners_screen_y)

        # 2. Determine the bounding box of the search area in the world grid.
        min_wx = max(0, int(np.min(world_corners[:, 0])) - 2)
        max_wx = min(self.world.gen.config.WIDTH, int(np.max(world_corners[:, 0])) + 2)
        min_wy = max(0, int(np.min(world_corners[:, 1])) - 2)
        max_wy = min(self.world.gen.config.HEIGHT, int(np.max(world_corners[:, 1])) + 2)

        # 3. Iterate only over tiles in the bounding box and check for intersection.
        tiles_in_rect = set()
        for x in range(min_wx, max_wx):
            for y in range(min_wy, max_wy):
                px, py = self.world_to_screen(x, y) # This already includes camera offset
                tile_points = [(px, py), (px + self.config.TILE_WIDTH // 2, py + self.config.TILE_HEIGHT // 2), (px, py + self.config.TILE_HEIGHT), (px - self.config.TILE_WIDTH // 2, py + self.config.TILE_HEIGHT // 2)]
                if selection_rect.collidepoint(tile_points[0]) or any(selection_rect.clipline(tile_points[i], tile_points[(i + 1) % 4]) for i in range(4)):
                    tiles_in_rect.add((x, y))
        return tiles_in_rect