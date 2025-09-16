import pygame
from camera import Camera
from world import World
from .pgi_tile_painter import PGITilePainter

class PGIWorldPainter(pygame.sprite.Group):
    """Top-down WorldPainter using sprites with efficient culling."""

    def __init__(self):
        super().__init__()
        self.world = World.get_instance()
        self.camera = Camera.get_instance()
        self.tile_sprites = {}  # (x, y) -> PGITilePainter

        self.surface = pygame.Surface(
            (self.camera.width_pxl, self.camera.height_pxl), pygame.SRCALPHA
        )

        self._visible_range = (0, 0, 0, 0)
        self._last_camera_state = (None, None, None)

    def _compute_visible_range(self):
        cam = self.camera
        if (cam.x, cam.y, cam.tile_size) == self._last_camera_state:
            return

        start_x = max(int(cam.x), 0)
        end_x = min(int(cam.x + cam.width_tls + 1), self.world.world_size_x)
        start_y = max(int(cam.y), 0)
        end_y = min(int(cam.y + cam.height_tls + 1), self.world.world_size_y)

        self._visible_range = (start_x, end_x, start_y, end_y)
        self._last_camera_state = (cam.x, cam.y, cam.tile_size)

    def update(self):
        """Update visible TilePainters and their positions."""
        self._compute_visible_range()
        start_x, end_x, start_y, end_y = self._visible_range
        tile_size = self.camera.tile_size

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                key = (x, y)
                tile = self.world.get_tile(x, y)
                if key not in self.tile_sprites:
                    sprite = PGITilePainter(tile, x, y)
                    sprite.update_image(tile_size)
                    sprite.update_position(self.camera)
                    self.tile_sprites[key] = sprite
                    super().add(sprite)
                else:
                    sprite = self.tile_sprites[key]
                    sprite.update_image(tile_size)
                    sprite.update_position(self.camera)

    def draw(self) -> pygame.Surface:
        """Draw only visible sprites onto self.surface using Group.draw()."""
        self.surface.fill((0, 0, 0, 0))
        # Create a temporary group for visible sprites
        start_x, end_x, start_y, end_y = self._visible_range
        visible_sprites = [
            self.tile_sprites[(x, y)]
            for y in range(start_y, end_y)
            for x in range(start_x, end_x)
            if (x, y) in self.tile_sprites
        ]
        # draw() requires a surface and optionally a rect dict (we ignore)
        pygame.sprite.Group(visible_sprites).draw(self.surface)
        return self.surface

    def reset(self):
        """Call this when the world regenerates."""
        self.tile_sprites.clear()
        self._last_cam_state = (None, None, None)
        self._visible_range = (0, 0, 0, 0)
