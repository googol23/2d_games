import pygame
from functools import cached_property
import math

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


    def control(self, dt:float, keys=None, events=None, mouse_pos=None):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_LEFT]:   # pan screen left
            dx -= 1
            dy += 1
        if keys[pygame.K_RIGHT]:  # pan screen right
            dx += 1
            dy -= 1
        if keys[pygame.K_UP]:     # pan screen up
            dx -= 1
            dy -= 1
        if keys[pygame.K_DOWN]:   # pan screen down
            dx += 1
            dy += 1

        # normalize if moving
        if dx != 0 or dy != 0:
            length = math.sqrt(dx*dx + dy*dy)
            dx /= length
            dy /= length
            self.x += dx * self.config.SPEED_TILES * dt
            self.y += dy * self.config.SPEED_TILES * dt

        logger.info(f"Camera position: x={self.x:.2f}, y={self.y:.2f}")



    # --- Coordinate transformations ---
    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        iso_x = ((world_x - self.x) - (world_y - self.y)) * 0.5 * self.tile_width_pxl  + self.iso_offset_x
        iso_y = ((world_x - self.x) + (world_y - self.y)) * 0.5 * self.tile_height_pxl + self.iso_offset_y

        return int(iso_x), int(iso_y)


    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        """
        Convert absolute screen pixel coordinates -> world (tile) coordinates
        accounting for iso_offset, screen offset, and camera pan.
        """
        half_w = 0.5 * self.tile_width_pxl
        half_h = 0.5 * self.tile_height_pxl

        # Adjust for screen center offset
        s_rel_x = screen_x - self.iso_offset_x
        s_rel_y = screen_y - self.iso_offset_y

        # Invert the isometric projection equations
        # s_rel_x = (w_rel_x - w_rel_y) * half_w
        # s_rel_y = (w_rel_x + w_rel_y) * half_h
        w_rel_x = (s_rel_x / half_w + s_rel_y / half_h) * 0.5
        w_rel_y = (s_rel_y / half_h - s_rel_x / half_w) * 0.5

        # Add camera's world position to get absolute world coordinates
        world_x = self.x + w_rel_x
        world_y = self.y + w_rel_y

        return world_x, world_y

    def get_visible_tile_bounds(self, margin: int = 2) -> tuple[int, int, int, int]:
        """
        Calculates the bounding box of visible tiles in world coordinates.
        Returns (min_x, max_x, min_y, max_y).
        """
        corners = [
            self.screen_to_world(0, 0),
            self.screen_to_world(self.screen_width, 0),
            self.screen_to_world(0, self.screen_height),
            self.screen_to_world(self.screen_width, self.screen_height),
        ]
        min_x = int(min(c[0] for c in corners)) - margin
        max_x = int(max(c[0] for c in corners)) + margin
        min_y = int(min(c[1] for c in corners)) - margin
        max_y = int(max(c[1] for c in corners)) + margin
        return min_x, max_x, min_y, max_y

    def get_visible_tiles(self, margin: int = 2) -> list[tuple[int, int]]:
        """
        Calculates the precise list of visible tiles by iterating in a transformed
        "diamond" coordinate space that maps directly to the screen.

        Returns a list of (x, y) world coordinates for visible tiles.
        """
        half_w = 0.5 * self.tile_width_pxl
        half_h = 0.5 * self.tile_height_pxl

        # The screen is a rectangle in screen-space. In world-space, this corresponds
        # to a diamond shape. By transforming our iteration space, we can treat the
        # visible diamond as a simple rectangle.
        # Let u = x + y and v = x - y.
        # These correspond directly to screen y and screen x, respectively.

        # Find the min/max of u = x + y
        u_min = (self.x + self.y) + (0 - self.iso_offset_y) / half_h
        u_max = (self.x + self.y) + (self.screen_height - self.iso_offset_y) / half_h

        # Find the min/max of v = x - y
        v_min = (self.x - self.y) + (0 - self.iso_offset_x) / half_w
        v_max = (self.x - self.y) + (self.screen_width - self.iso_offset_x) / half_w

        visible_tiles = []
        # Iterate over the diamond space, including a margin
        for u in range(int(u_min) - margin, int(u_max) + margin):
            for v in range(int(v_min) - margin, int(v_max) + margin):
                # We only need to check tiles where u and v have the same parity
                # because x = (u+v)/2 and y = (u-v)/2 must be integers.
                if (u + v) % 2 == 0:
                    # Convert back to world coordinates
                    x = (u + v) // 2
                    y = (u - v) // 2
                    visible_tiles.append((x, y))

        return visible_tiles