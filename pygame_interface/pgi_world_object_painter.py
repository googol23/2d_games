import pygame
from camera import Camera
from world_object import WorldObject
from pathlib import Path

class PGIWorldObjectPainter(pygame.sprite.Sprite):
    """
    Sprite wrapper for a WorldObject.
    Loads texture once at init; falls back to a colored rectangle.
    Draws the object's name above the rectangle/texture.
    """

    def __init__(self, obj: WorldObject):
        super().__init__()
        self.obj = obj
        self.camera = Camera.get_instance()
        self.image = None
        self.rect = None

        # Load texture once
        self._texture = None
        if hasattr(self.obj, "texture") and self.obj.texture:
            path = Path(self.obj.texture)
            if path.is_file():
                try:
                    loaded = pygame.image.load(str(path)).convert_alpha()
                    self._texture = loaded
                except Exception as e:
                    print(f"Failed to load texture {self.obj.texture}: {e}")

        self.update_image(self.camera.tile_size)
        self.update_position(self.camera)

    def update_image(self, tile_size: int):
        """
        Update sprite image based on tile_size.
        Uses cached texture if available, otherwise draws a rectangle.
        Draws the object's name above the figure.
        """
        # Font for the name
        font_size = max(12, self.camera.height_pxl // 40)
        font = pygame.font.SysFont(None, font_size)
        obj_name = str(getattr(self.obj, "name", f"{self.obj.x},{self.obj.y}"))
        text_surface = font.render(obj_name, True, (255, 255, 255))

        # Surface size: width is max(tile_size, text width), height = tile_size + text height
        surface_width = max(tile_size, text_surface.get_width())
        total_height = tile_size + text_surface.get_height()
        self.image = pygame.Surface((surface_width, total_height), pygame.SRCALPHA)

        shape_x = (surface_width - tile_size) // 2
        shape_y = text_surface.get_height()

        # Draw object: texture or rectangle
        if self._texture:
            texture_scaled = pygame.transform.smoothscale(self._texture, (tile_size, tile_size))
            self.image.blit(texture_scaled, (shape_x, shape_y))
        else:
            color = getattr(self.obj, "color", (255, 0, 0))
            pygame.draw.rect(self.image, color, pygame.Rect(shape_x, shape_y, tile_size, tile_size))

        # Draw name above
        text_x = (surface_width - text_surface.get_width()) // 2
        self.image.blit(text_surface, (text_x, 0))

        # Update rect
        self.rect = self.image.get_rect()

    def update_position(self, camera: Camera):
        """
        Position the sprite on the screen based on camera.
        Bottom of rectangle/image aligns with world coordinates.
        """
        screen_x = (self.obj.x - camera.x) * camera.tile_size
        screen_y = (self.obj.y - camera.y) * camera.tile_size
        self.rect.topleft = (int(screen_x), int(screen_y + self.rect.height - camera.tile_size))
