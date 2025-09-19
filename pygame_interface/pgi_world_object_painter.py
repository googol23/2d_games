import pygame
from camera import Camera
from world_object import WorldObject
from pathlib import Path
from manager import Manager
from .pgi_texture_registry import SURFACE_CACHE,preload_texture_zoom_levels
import logging
logger = logging.getLogger("pgi")
import pygame
from camera import Camera
from world_object import WorldObject
from pathlib import Path
from manager import Manager
import logging

logger = logging.getLogger("pgi")


class PGIWorldObjectPainter(pygame.sprite.Sprite):
    def __init__(self, obj: WorldObject, manager: Manager):
        super().__init__()
        self.obj = obj
        self.manager: Manager = manager
        self.camera: Camera = Camera.get_instance()
        self.image = None
        self.rect = None

        self._texture_id: int | None = None
        if hasattr(self.obj, "texture") and self.obj.texture:
            path = Path(self.obj.texture)
            if path.is_file():
                try:
                    self._texture_id = preload_texture_zoom_levels(str(path))
                except Exception as e:
                    logger.warning(f"Failed to load texture {self.obj.texture}: {e}")

        self.update_image(self.camera.tile_size)
        self.update_position(self.camera)

    def update_image(self, tile_size: int):
        font_size = max(12, self.camera.height_pxl // 40)
        font = pygame.font.SysFont(None, font_size)
        obj_name = str(getattr(self.obj, "name", f"{self.obj.x},{self.obj.y}"))
        text_surface = font.render(obj_name, True, (255, 255, 255))

        surface_width = max(tile_size, text_surface.get_width())
        total_height = tile_size + text_surface.get_height()
        self.image = pygame.Surface((surface_width, total_height), pygame.SRCALPHA)

        shape_x = (surface_width - tile_size) // 2
        shape_y = text_surface.get_height()

        # Draw object using precomputed surface if available
        if self._texture_id is not None:
            scaled_surface = SURFACE_CACHE.get((self._texture_id, tile_size))
            if scaled_surface:
                self.image.blit(scaled_surface, (shape_x, shape_y))
            else:
                # fallback to rectangle if surface missing
                color = getattr(self.obj, "color", (255, 0, 0))
                pygame.draw.rect(self.image, color, pygame.Rect(shape_x, shape_y, tile_size, tile_size))
        else:
            color = getattr(self.obj, "color", (255, 0, 0))
            pygame.draw.rect(self.image, color, pygame.Rect(shape_x, shape_y, tile_size, tile_size))

        # Draw name above
        text_x = (surface_width - text_surface.get_width()) // 2
        self.image.blit(text_surface, (text_x, 0))

        # Red border if selected
        if getattr(self.obj, "id", None) in self.manager.selection:
            border_rect = pygame.Rect(shape_x, shape_y, tile_size, tile_size)
            pygame.draw.rect(self.image, (0, 0, 255), border_rect, width=2)

        screen_x, screen_y = self.camera.world_to_screen(self.obj.x, self.obj.y)
        self.rect = self.image.get_rect(center=(screen_x, screen_y))

    def update_position(self, camera: Camera):
        screen_x = (self.obj.x - camera.x) * camera.tile_size
        screen_y = (self.obj.y - camera.y) * camera.tile_size
        self.rect.topleft = (int(screen_x), int(screen_y + self.rect.height - camera.tile_size))
