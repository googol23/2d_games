from world import World
from typing_extensions import Self
from functools import cached_property

class CameraConfig:
    def __init__(self,
                 speed_tiles:float=0.1,
                 zoom_step:int = 2,
                 pan_edge_size:int = 10,
                 min_tile_size = 8,
                 max_tile_size = 32,
                 iso_view:bool = False):
        self.SPEED_TILES:float = speed_tiles # Percentual of the curret visible tiles
        self.ZOOM_STEP = zoom_step
        self.MIN_TILE_SIZE = min_tile_size
        self.MAX_TILE_SIZE = max_tile_size
        self.PAN_EDGE_SIZE = pan_edge_size
        self.ISO_VIEW = iso_view

class Camera:
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

    def __init__(self,
                 x:float=0,
                 y:float=0,
                 width_pxl:int=800,
                 height_pxl:int=600,
                 tile_size:int=5,
                 config: CameraConfig | None = None):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self.world = World.get_instance()
        self.x = x
        self.y = y
        self.width_pxl = width_pxl
        self.height_pxl = height_pxl

        self.config = config if config is not None else CameraConfig()

        self.tile_size = max(self.config.MIN_TILE_SIZE,
                            min(tile_size, self.config.MAX_TILE_SIZE))

        self.width_tls = self.width_pxl / self.tile_size
        self.height_tls = self.height_pxl / self.tile_size

        # view counts in tiles
        self._update_view_counts()

        # iso dimensions (floats)
        self._update_iso_dims()

    # ---------------- helpers ----------------
    def _update_view_counts(self):
        self.width_tls = float(self.width_pxl) / float(self.tile_size)
        self.height_tls = float(self.height_pxl) / float(self.tile_size)

    def _update_iso_dims(self):
        # Keep floats to avoid integer truncation
        self.iso_tile_w = float(self.tile_size * 2.0)   # full diamond width
        self.iso_tile_h = float(self.tile_size)         # full diamond height
        self.iso_half_w = self.iso_tile_w / 2.0         # tile_size
        self.iso_half_h = self.iso_tile_h / 2.0         # tile_size / 2

    def _cam_pixel_offset(self) -> tuple[float, float]:
        """
        Pixel offset of camera origin (world tile self.x, self.y) in isometric pixel space.
        cam_px = (cx - cy) * half_w
        cam_py = (cx + cy) * half_h
        """
        cam_px = (self.x - self.y) * self.iso_half_w
        cam_py = (self.x + self.y) * self.iso_half_h
        return cam_px, cam_py

    def _world_size(self) -> tuple[float, float]:
        w = getattr(self.world, "world_size_x", None)
        h = getattr(self.world, "world_size_y", None)
        if w is None or h is None:
            w = getattr(self.world, "width", w)
            h = getattr(self.world, "height", h)
        if w is None or h is None:
            raise AttributeError("World object missing width/height attributes")
        return float(w), float(h)

    # --- Coordinate conversion (orthographic) ---
    def world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        screen_x = (world_x - self.x) * self.tile_size
        screen_y = (world_y - self.y) * self.tile_size
        return screen_x, screen_y

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        return screen_x / self.tile_size + self.x, screen_y / self.tile_size + self.y

    # --- Isometric conversions ---
    def world_to_screen_iso(self, world_x: float, world_y: float) -> tuple[int, int]:
        """
        grid -> screen (isometric). Returns top vertex of the diamond in screen coords.
        """
        screen_x = (world_x - world_y) * self.iso_half_w - self.x * self.iso_half_w * 2
        screen_y = (world_x + world_y) * self.iso_half_h - self.y * self.iso_half_h * 2

        # Add offsets to align the map properly on screen
        offset_x = self.width_pxl // 2  # center horizontally
        offset_y = 0                     # adjust vertically if needed

        return int(round(screen_x + offset_x)), int(round(screen_y + offset_y))


    def screen_to_world_iso(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        """
        screen px -> fractional world grid coords (isometric).
        """
        # Apply the same offset before inverting the isometric projection
        offset_x = self.width_pxl // 2
        offset_y = 0

        wx = screen_x - offset_x + self.x * self.tile_size
        wy = screen_y - offset_y + self.y * self.tile_size

        world_x = (wx / self.iso_half_w + wy / self.iso_half_h) * 0.5
        world_y = (wy / self.iso_half_h - wx / self.iso_half_w) * 0.5
        return world_x, world_y


    def in_view(self, world_x: float, world_y: float) -> bool:
        """
        Check if a world coordinate (x, y) is within the camera's current view.

        :param x: World x coordinate
        :param y: World y coordinate
        :return: True if (x, y) is inside camera view, False otherwise
        """
        if self.config.ISO_VIEW:
            sw, sh = self.width_pxl, self.height_pxl

            # convert screen corners to world grid coords (floats)
            corners = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
            gxs, gys = [], []
            for cx, cy in corners:
                gx, gy = self.screen_to_world_iso(cx, cy)
                gxs.append(gx)
                gys.append(gy)

            # bounds remain floats
            margin = 2.0
            min_x = max(0.0, min(gxs) - margin)
            max_x = min(self.world.world_size_x,  max(gxs) + margin)
            min_y = max(0.0, min(gys) - margin)
            max_y = min(self.world.world_size_y, max(gys) + margin)

            return (min_x <= world_x <= max_x) and (min_y <= world_y <= max_y)
        else:
            return (
                self.x <= world_x < self.x + self.width_tls and
                self.y <= world_y < self.y + self.height_tls
            )

    # --- Movement ---
    def move(self, dx:int, dy:int ):
        """Move camera in tile units and clamp to world bounds"""
        speed_x = self.config.SPEED_TILES * self.width_tls
        speed_y = self.config.SPEED_TILES * self.height_tls
        self.x = max(0, min(self.x + dx*speed_x, self.world.world_size_x - self.width_tls))
        self.y = max(0, min(self.y + dy*speed_y, self.world.world_size_y - self.height_tls))

    def pan(self, dir_x: int, dir_y: int):
        step_x = self.config.SPEED_TILES * self.width_tls * dir_x
        step_y = self.config.SPEED_TILES * self.height_tls * dir_y
        self.move(step_x, step_y)

    def edge_pan(self, mx: int, my: int):
        dx_sign = -1 if mx < self.config.PAN_EDGE_SIZE else 1 if mx > self.width_pxl - self.config.PAN_EDGE_SIZE else 0
        dy_sign = -1 if my < self.config.PAN_EDGE_SIZE else 1 if my > self.height_pxl - self.config.PAN_EDGE_SIZE else 0
        if dx_sign != 0 or dy_sign != 0:
            self.pan(dx_sign, dy_sign)

    # --- Zoom ---
    def zoom(self, direction: int = 1):
        self.tile_size = max(self.config.MIN_TILE_SIZE,
                             min(self.tile_size + direction * self.config.ZOOM_STEP,
                                 self.config.MAX_TILE_SIZE))
        # clamp camera to world
        w, h = self._world_size()
        self.x = max(0.0, min(self.x, w - self.width_tls))
        self.y = max(0.0, min(self.y, h - self.height_tls))
