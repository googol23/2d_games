from world import World
import controls
from typing_extensions import Self

class CameraConfig:
    def __init__(self,
                 speed_tiles:float=0.1,
                 zoom_step:int = 2,
                 pan_edge_size:int = 10,
                 min_tile_size = 10,
                 max_tile_size = 100):
        self.SPEED_TILES:float = speed_tiles # Percentual of the curret visible tiles
        self.ZOOM_STEP = zoom_step
        self.MIN_TILE_SIZE = min_tile_size
        self.MAX_TILE_SIZE = max_tile_size
        self.PAN_EDGE_SIZE = pan_edge_size

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
                 tile_size=5,
                 config: CameraConfig | None = None):
        """
        :param world: World object reference
        :param x, y: camera position in tiles (top-left)
        :param width_pxl, height_pxl: camera size in pixels
        :param tile_size: pixels per tile
        """
        self.world = World.get_instance()
        self.x = x
        self.y = y
        self.width_pxl = width_pxl
        self.height_pxl = height_pxl
        self.tile_size = tile_size

        self.width_tls = self.width_pxl / self.tile_size
        self.height_tls = self.height_pxl / self.tile_size

        self.config = config if config is not None else CameraConfig()

        self.iso_tile_w = tile_size * 2   # full width
        self.iso_tile_h = tile_size       # full height
        self.iso_half_w = tile_size       # half width
        self.iso_half_h = tile_size // 2  # half height


    # --- Coordinate conversion ---
    def world_to_screen(self, world_x:float, world_y:float) -> tuple[float,float]:
        """
        world_x,world_x : world grid coords
        returns: (screen_x, screen_y) coordinates (ortographic square tile top view)
        """
        screen_x = (world_x - self.x) * self.tile_size
        screen_y = (world_y - self.y) * self.tile_size
        return screen_x, screen_y

    def screen_to_world(self, screen_x:int, screen_y:int) -> tuple[float,float]:
        """
        Convert screen pixel coords -> grid coordinates (can be fractional).
        """
        world_x = screen_x / self.tile_size + self.x
        world_y = screen_y / self.tile_size + self.y
        return world_x, world_y

    def world_to_screen_iso(self, world_x: float, world_y: float) -> tuple[int, int]:
        """
        Convert grid coordinates -> screen pixel coords (isometric).
        Returns top vertex of the tile diamond.
        """
        screen_x = (world_x - world_y) * self.iso_half_w - self.x * self.tile_size
        screen_y = (world_x + world_y) * self.iso_half_h - self.y * self.tile_size
        return int(round(screen_x)), int(round(screen_y))


    def screen_to_world_iso(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        """
        Convert screen pixel coords in isometric view -> grid coordinates (can be fractional).
        """
        wx = screen_x + self.x * self.tile_size
        wy = screen_y + self.y * self.tile_size
        world_x = (wx / self.iso_half_w + wy / self.iso_half_h) * 0.5
        world_y = (wy / self.iso_half_h - wx / self.iso_half_w) * 0.5
        return world_x, world_y


    def in_view(self, x: float, y: float) -> bool:
        """
        Check if a world coordinate (x, y) is within the camera's current view.

        :param x: World x coordinate
        :param y: World y coordinate
        :return: True if (x, y) is inside camera view, False otherwise
        """
        return (
            self.x <= x < self.x + self.width_tls and
            self.y <= y < self.y + self.height_tls
        )

    def in_view_iso(self, world_x:float, world_y: float)-> bool:
        """
        Check if a world coordinate (x, y) is within the camera's current view.
        This is use for a isometric top-down rendering

        :param world_x: World x coordinate
        :param world_y: World y coordinate
        :return: True if (world_x, world_y) is inside camera view, False otherwise
        """
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
        max_x = min(self.world.width,  max(gxs) + margin)
        min_y = max(0.0, min(gys) - margin)
        max_y = min(self.world.height, max(gys) + margin)

        return (min_x <= world_x <= max_x) and (min_y <= world_y <= max_y)


    # --- Movement ---
    def move(self, dx:int, dy:int ):
        """Move camera in tile units and clamp to world bounds"""
        speed_x = self.config.SPEED_TILES * self.width_tls
        speed_y = self.config.SPEED_TILES * self.height_tls
        self.x = max(0, min(self.x + dx*speed_x, self.world.world_size_x - self.width_tls))
        self.y = max(0, min(self.y + dy*speed_y, self.world.world_size_y - self.height_tls))

    # --- Mouse-edge panning ---
    def edge_pan(self, mx, my):
        """
        Pan the camera when mouse is near edges.
        :param mx: mouse x (px)
        :param my: mouse y (px)
        :param factor: fraction of visible tiles to move per frame
        """
        speed_x = self.width_tls  * self.config.SPEED_TILES
        speed_y = self.height_tls * self.config.SPEED_TILES

        dx = 0
        dy = 0
        if mx < self.config.PAN_EDGE_SIZE:
            dx = -speed_x
        elif mx > self.width_pxl - self.config.PAN_EDGE_SIZE:
            dx = speed_x

        if my < self.config.PAN_EDGE_SIZE:
            dy = -speed_y
        elif my > self.height_pxl - self.config.PAN_EDGE_SIZE:
            dy = speed_y

        self.move(dx, dy)

    # --- Zoom ---
    def zoom(self, direction:int = 1):
        """
        Zoom in/out camera by changing tile_size while keeping top-left position
        :param direction: +1 = zoom in, -1 = zoom out
        """
        self.tile_size = max(self.config.MIN_TILE_SIZE, min(self.tile_size + direction*self.config.ZOOM_STEP, self.config.MAX_TILE_SIZE))
        # Update visible tiles
        self.width_tls = self.width_pxl / self.tile_size
        self.height_tls = self.height_pxl / self.tile_size
        # Clamp to world
        self.x = max(0, min(self.x, self.world.world_size_x - self.width_tls))
        self.y = max(0, min(self.y, self.world.world_size_y - self.height_tls))
