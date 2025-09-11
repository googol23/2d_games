import controls

class CameraConfig:
    def __init__(self,
                 speed_tiles:float=0.1,
                 zoom_step:int = 2,
                 min_tile_size = 10,
                 max_tile_size = 100):
        self.SPEED_TILES:float = speed_tiles # Percentual of the curret visible tiles
        self.ZOOM_STEP = zoom_step
        self.MIN_TILE_SIZE = min_tile_size
        self.MAX_TILE_SIZE = max_tile_size

class Camera:
    def __init__(self,
                 world,
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
        self.world = world
        self.x = x
        self.y = y
        self.width_pxl = width_pxl
        self.height_pxl = height_pxl
        self.tile_size = tile_size

        # Compute visible tiles
        self.width_tls = self.width_pxl / self.tile_size
        self.height_tls = self.height_pxl / self.tile_size

        self.config = config if config is not None else CameraConfig()

    # --- Coordinate conversion ---
    def world_to_screen(self, world_x:float, world_y:float) -> tuple[float,float]:
        screen_x = (world_x - self.x) * self.tile_size
        screen_y = (world_y - self.y) * self.tile_size
        return screen_x, screen_y

    def screen_to_world(self, screen_x:int, screen_y:int) -> tuple[float,float]:
        world_x = screen_x / self.tile_size + self.x
        world_y = screen_y / self.tile_size + self.y
        return world_x, world_y

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
        if mx < controls.PAN_EDGE_SIZE:
            dx = -speed_x
        elif mx > self.width_pxl - controls.PAN_EDGE_SIZE:
            dx = speed_x

        if my < controls.PAN_EDGE_SIZE:
            dy = -speed_y
        elif my > self.height_pxl - controls.PAN_EDGE_SIZE:
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

    def in_view(self, x: float, y: float):
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