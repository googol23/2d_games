import pygame
from world_object import WorldObject
from camera import Camera
from functools import cached_property


class PGIWorldObjectPainter(pygame.sprite.Sprite):
    def __init__(self, world_obj: WorldObject):
        super().__init__()
        self.world_obj = world_obj
        self._last_tile_size = None
        self._last_name = None
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    @cached_property
    def font(self):
        """Cache the font object globally, fonts are expensive to recreate."""
        return pygame.font.SysFont(None, 24)

    def _make_surface(self, tile_size: int) -> pygame.Surface:
        """Create the rendered surface for the object at a given tile size."""
        name = getattr(self.world_obj, "name", type(self.world_obj).__name__)
        text_surf = self.font.render(name, True, (255, 255, 255))

        # Determine surface size
        width = max(tile_size, text_surf.get_width())
        height = tile_size + text_surf.get_height()
        surf = pygame.Surface((width, height), pygame.SRCALPHA)

        if getattr(self.world_obj, "texture", None):
            # If the object has a texture, use it
            texture = pygame.transform.scale(self.world_obj.texture, (tile_size, tile_size))
            surf.blit(texture, (0, text_surf.get_height()))
        else:
            # Draw placeholder triangle
            triangle_height = tile_size
            triangle_width = tile_size
            points = [
                (triangle_width // 2, text_surf.get_height()),             # top vertex
                (0, text_surf.get_height() + triangle_height),            # bottom-left
                (triangle_width, text_surf.get_height() + triangle_height)  # bottom-right
            ]
            color = getattr(self.world_obj, "dummy_render_color", (200, 50, 50))
            pygame.draw.polygon(surf, color, points)

        # Draw the object’s name on top
        surf.blit(text_surf, (0, 0))
        return surf

    def update(self):
        camera = Camera.get_instance()
        tile_size = camera.tile_size
        name = getattr(self.world_obj, "name", type(self.world_obj).__name__)

        # Only recreate surface if tile size or object name changed
        if tile_size != self._last_tile_size or name != self._last_name:
            self.image = self._make_surface(tile_size)
            self._last_tile_size = tile_size
            self._last_name = name
            self.rect = self.image.get_rect()

        # Update position every frame so the bottom-left of the rectangle matches world coordinates
        screen_x, screen_y = camera.world_to_screen(self.world_obj.x, self.world_obj.y)
        # offset Y so the rectangle sits below the text
        self.rect.topleft = (screen_x, screen_y - self.font.get_height())
