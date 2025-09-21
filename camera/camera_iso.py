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
    def offset_x(self) -> int:
        return self.screen_width // 2 - self.world_width_pxl

    @cached_property
    def offset_y(self) -> int:
        return 0

    @cached_property
    def iso_offset_x(self) -> int:
        return (self.world.size_y - 1) * (self.tile_width_pxl // 2) if self.world else 0

    @cached_property
    def iso_offset_y(self) -> int:
        return 5*self.tile_height_pxl  # vertical padding

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
    def world_to_pixel(self, world_x: float, world_y: float) -> tuple[int, int]:
        """
        Convert world (tile) coordinates to pixel coordinates on a surface
        with only isometric math and isometric offset (for world_surface).
        """
        iso_x = (world_x - world_y) * 0.5 * self.tile_width_pxl
        iso_y = (world_x + world_y) * 0.5 * self.tile_height_pxl
        return int(iso_x + self.iso_offset_x), int(iso_y + self.iso_offset_y)

    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        iso_x, iso_y = self.world_to_pixel(world_x, world_y)
        # Camera offset for panning/zooming
        iso_x -= (self.x - self.y) * 0.5 * self.tile_width_pxl
        iso_y -= (self.x + self.y) * 0.5 * self.tile_height_pxl
        iso_x += self.offset_x
        iso_y += self.offset_y
        return int(iso_x), int(iso_y)


    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        """Convert screen pixels to world coordinates (tiles) relative to camera."""
        world_x = ((screen_x / (0.5 * self.tile_width_pxl)) + (screen_y / (0.5 * self.tile_height_pxl))) / 2 + self.x
        world_y = ((screen_y / (0.5 * self.tile_height_pxl)) - (screen_x / (0.5 * self.tile_width_pxl))) / 2 + self.y
        return world_x, world_y
