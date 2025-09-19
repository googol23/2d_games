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

    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        width_pxl: int = 800,
        height_pxl: int = 600,
        tile_size: int = 5,
        config: CameraConfig | None = None,
    ):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self.world = World.get_instance()
        self.x = x
        self.y = y
        self.width_pxl = width_pxl
        self.height_pxl = height_pxl
        self.config = config or CameraConfig()

        # Clamp initial tile size
        self.tile_size = max(
            self.config.MIN_TILE_SIZE, min(tile_size, self.config.MAX_TILE_SIZE)
        )

    # ---------------- properties ----------------
    @property
    def width_tls(self) -> float:
        """Number of tiles visible horizontally"""
        return self.width_pxl / self.tile_size

    @property
    def height_tls(self) -> float:
        """Number of tiles visible vertically"""
        return self.height_pxl / self.tile_size

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
        dx = -1 if mx < self.config.PAN_EDGE_SIZE else 1 if mx > self.width_pxl - self.config.PAN_EDGE_SIZE else 0
        dy = -1 if my < self.config.PAN_EDGE_SIZE else 1 if my > self.height_pxl - self.config.PAN_EDGE_SIZE else 0
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
