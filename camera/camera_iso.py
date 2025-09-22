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


    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        """
        Convert absolute screen pixel coordinates -> world (tile) coordinates
        accounting for iso_offset, screen offset, and camera pan.
        """
        half_w = 0.5 * self.tile_width_pxl
        half_h = 0.5 * self.tile_height_pxl

        # undo what world_to_screen applies:
        # world_to_screen: iso = world_to_pixel(...) - cam_pan + offset
        # so to invert: subtract offset, subtract iso_offset, add cam_pan contribution
        sx = screen_x - self.offset_x - self.iso_offset_x + (self.x - self.y) * half_w
        sy = screen_y - self.offset_y - self.iso_offset_y + (self.x + self.y) * half_h

        # now invert isometric transform:
        world_x = (sx / half_w + sy / half_h) * 0.5
        world_y = (sy / half_h - sx / half_w) * 0.5

        return world_x, world_y


    import math

    def visible_tiles(self, margin:int = 1) -> list[tuple[int,int]]:
        """
        Return list of (x,y) tile coordinates that are at least partially visible
        on the screen. Efficient: computes world-space bounding box from screen
        corners then culls tiles whose iso bounding box doesn't intersect the screen.
        margin: extra tiles to include around the bbox (helps for rounding).
        """
        if not self.world:
            return []

        w, h = self.screen_width, self.screen_height

        # screen corners in absolute screen coords
        screen_corners = [(0,0), (w,0), (0,h), (w,h)]

        # convert to world-space (floats)
        corners_world = [self.screen_to_world(sx, sy) for sx, sy in screen_corners]
        xs = [c[0] for c in corners_world]
        ys = [c[1] for c in corners_world]

        # conservative integer bbox in tile space
        min_x = max(0, int(math.floor(min(xs))) - margin)
        max_x = min(self.world.size_x - 1, int(math.ceil(max(xs))) + margin)
        min_y = max(0, int(math.floor(min(ys))) - margin)
        max_y = min(self.world.size_y - 1, int(math.ceil(max(ys))) + margin)

        visible = []
        # small loop: only tiles inside the candidate bbox
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                # compute tile's 2D screen bbox using corners (fast)
                tl = self.world_to_screen(x, y)
                br = self.world_to_screen(x + 1, y + 1)
                left = min(tl[0], br[0])
                right = max(tl[0], br[0])
                top = min(tl[1], br[1])
                bottom = max(tl[1], br[1])

                # quick rectangle intersection test (partial visibility)
                if right < 0 or left > w or bottom < 0 or top > h:
                    continue
                visible.append((x, y))

        return visible