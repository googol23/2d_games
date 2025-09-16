import pygame
from world import World, Tile
from camera.camera import Camera
from .pgi_tile_painter import PGITilePainter
from typing_extensions import Self

class PGIWorldPainter:
    _self: Self | None = None

    def __new__(cls, *args, **kwargs):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    @classmethod
    def get_instance(cls):
        if cls._self is None:
            raise RuntimeError("Camera not created yet")
        return cls._self

    def __init__(self, progress_callback=None):
        self.world = World.get_instance()
        self.camera = Camera.get_instance()
        self.tile_painters = {}  # cached PGITilePainter per tile
        # --- Caching for visible tiles ---
        self._iso_positions_cache = {}
        self._top_positions_cache = {}
        self._last_cam_x = self.camera.x
        self._last_cam_y = self.camera.y
        self._last_tile_size = self.camera.tile_size

        self.progress_callback = progress_callback

    def get_tile_painter(self, x: int, y: int, tile: Tile):
        key = (x, y)
        if key not in self.tile_painters:
            self.tile_painters[key] = PGITilePainter(tile)
        return self.tile_painters[key]

    # --- Update cached visible tile positions ---
    def _update_iso_cache(self):
        cam = self.camera
        # Only update if camera moved or zoom changed
        if (cam.x, cam.y, cam.tile_size) == (self._last_cam_x, self._last_cam_y, self._last_tile_size):
            return  # no update needed

        sw, sh = cam.width_pxl, cam.height_pxl
        corners = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
        gxs, gys = [], []
        for sx, sy in corners:
            gx, gy = cam.screen_to_world_iso(sx, sy)
            gxs.append(gx)
            gys.append(gy)
        margin = 2
        min_x = max(0, int(min(gxs) - margin))
        max_x = min(self.world.world_size_x - 1, int(max(gxs) + margin))
        min_y = max(0, int(min(gys) - margin))
        max_y = min(self.world.world_size_y - 1, int(max(gys) + margin))

        self._iso_positions_cache.clear()
        count = 0
        total_tiles = (max_x - min_x + 1) * (max_y - min_y + 1)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                sx, sy = cam.world_to_screen_iso(x, y)
                self._iso_positions_cache[(x, y)] = (sx, sy)

                count += 1
                if self.progress_callback:
                    self.progress_callback(count, total_tiles)

        # Save current camera state
        self._last_cam_x, self._last_cam_y, self._last_tile_size = cam.x, cam.y, cam.tile_size

    def _update_top_cache(self):
        cam = self.camera
        if (cam.x, cam.y, cam.tile_size) == (self._last_cam_x, self._last_cam_y, self._last_tile_size):
            return  # no update needed

        start_x = max(int(cam.x), 0)
        end_x   = min(int(cam.x + cam.width_tls + 1), self.world.world_size_x)
        start_y = max(int(cam.y), 0)
        end_y   = min(int(cam.y + cam.height_tls + 1), self.world.world_size_y)

        self._top_positions_cache.clear()
        tile_size = cam.tile_size
        count = 0
        total_tiles = (start_y - end_y + 1) * (start_x - end_x + 1)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                sx = round((x - cam.x) * tile_size)
                sy = round((y - cam.y) * tile_size)
                self._top_positions_cache[(x, y)] = (sx, sy)

                count += 1
                if self.progress_callback:
                    self.progress_callback(count, total_tiles)

        self._last_cam_x, self._last_cam_y, self._last_tile_size = cam.x, cam.y, cam.tile_size

    def precompute(self, iso_view: bool = False):
        """Precompute tile positions so the first render is instant."""
        if iso_view:
            self._update_iso_cache()
        else:
            self._update_top_cache()

    # --- Main render ---
    def render(self, surface: pygame.Surface, iso_view: bool = False):
        surface.fill((0, 0, 0))
        if iso_view:
            self._update_iso_cache()
            for (x, y), (sx, sy) in self._iso_positions_cache.items():
                if not self.camera.in_view(x, y):
                    continue
                tile = self.world.get_tile(x, y)
                painter = self.get_tile_painter(x, y, tile)
                painter.update_iso(surface, x, y)
        else:
            self._update_top_cache()
            for (x, y), (sx, sy) in self._top_positions_cache.items():
                if not self.camera.in_view(x, y):
                    continue
                tile = self.world.get_tile(x, y)
                painter = self.get_tile_painter(x, y, tile)
                painter.update_top(surface, x, y)
