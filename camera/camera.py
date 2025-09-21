from world import World
from typing_extensions import Self


class CameraConfig:
    def __init__(
        self,
        speed_tiles: float = 0.1,
        zoom_step: int = 24,
        pan_edge_size: int = 10,
        min_tile_size: int = 64,
        max_tile_size: int = 256,
    ):
        self.SPEED_TILES = speed_tiles      # Percent of visible tiles per move
        self.ZOOM_STEP = zoom_step
        self.MIN_TILE_SIZE = min_tile_size
        self.MAX_TILE_SIZE = max_tile_size
        self.PAN_EDGE_SIZE = pan_edge_size


class Camera:
    def __init__(
        self,
        world: World | None = None,
        start_x: float = 0,    # in world tile coords
        start_y: float = 0,    # in world tile coords
        screen_width_pxl: int = 800,  # screen width in pixels
        screen_height_pxl: int = 600, # screen height in pixels
        tile_size_w: int = 5, # TODO I DON'T LIKE THIS, becuase it doe noto fit for ISO view
        config: CameraConfig | None = None,
    ):

        self.world = world
        self.x = start_x
        self.y = start_y
        self.screen_width_pxl = screen_width_pxl
        self.screen_height_pxl = screen_height_pxl
        self.config = config or CameraConfig()

        # Clamp initial tile size
        self.tile_size = max(
            self.config.MIN_TILE_SIZE, min(tile_size, self.config.MAX_TILE_SIZE)
        )

    # ---------------- properties ----------------
    @property
    def width_tls(self) -> float:
        """Number of tiles visible horizontally"""
        return self.screen_width_pxl / self.tile_size

    @property
    def height_tls(self) -> float:
        """Number of tiles visible vertically"""
        return self.screen_height_pxl / self.tile_size

    @property
    def world_width(self) -> float:
        return float(getattr(self.world, "size_x", getattr(self.world, "width", 0)))

    @property
    def world_height(self) -> float:
        return float(getattr(self.world, "size_y", getattr(self.world, "height", 0)))

    # ---------------- coordinate conversion ----------------
    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        """Convert world tile coords to screen pixels."""
        return round((world_x - self.x) * self.tile_size), round((world_y - self.y) * self.tile_size)

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        """Convert screen pixels to world tile coords."""
        return screen_x / self.tile_size + self.x, screen_y / self.tile_size + self.y

    def in_view(self, world_x: float, world_y: float) -> bool:
        """Check if a world coordinate is within the camera's current view."""
        return (
            self.x <= world_x < self.x + self.width_tls
            and self.y <= world_y < self.y + self.height_tls
        )

    # ---------------- movement ----------------
    def move(self, dx: float, dy: float):
        """Move camera in tile units and clamp to world bounds."""
        speed_x = self.config.SPEED_TILES * self.width_tls
        speed_y = self.config.SPEED_TILES * self.height_tls
        self.x = max(0.0, min(self.x + dx * speed_x, self.world_width - self.width_tls))
        self.y = max(0.0, min(self.y + dy * speed_y, self.world_height - self.height_tls))

    def pan(self, dir_x: int, dir_y: int):
        """Pan camera in direction (dir_x, dir_y)."""
        self.move(dir_x, dir_y)

    def edge_pan(self, mx: int, my: int):
        """Pan camera if mouse is near screen edges."""
        dx = -1 if mx < self.config.PAN_EDGE_SIZE else 1 if mx > self.screen_width_pxl - self.config.PAN_EDGE_SIZE else 0
        dy = -1 if my < self.config.PAN_EDGE_SIZE else 1 if my > self.screen_height_pxl - self.config.PAN_EDGE_SIZE else 0
        if dx != 0 or dy != 0:
            self.pan(dx, dy)

    # ---------------- zoom ----------------
    def zoom(self, direction: int = 1):
        """Zoom in/out by changing tile size."""
        self.tile_size = max(
            self.config.MIN_TILE_SIZE,
            min(self.tile_size + direction * self.config.ZOOM_STEP, self.config.MAX_TILE_SIZE),
        )
        # Clamp camera position to world bounds after zoom
        self.x = max(0.0, min(self.x, self.world_width - self.width_tls))
        self.y = max(0.0, min(self.y, self.world_height - self.height_tls))
