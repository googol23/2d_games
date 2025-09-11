import pygame
from camera import Camera
import itertools

class WorldObject:
    def __init__(self, x, y):
        self.id = itertools.count()
        self.x = float(x)
        self.y = float(y)
        self.needs_redraw = True
        self.dummy_render_color = (255,0,0)
        self.texture = None

    @property
    def tile(self):
        return int(self.x), int(self.y)

    def update_position(self,x,y):
        self.x = float(x)
        self.y = float(y)
        self.needs_redraw = True

    def render(self, surface, camera: Camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        tile_size = camera.tile_size
        class_name = type(self).__name__
        if hasattr(self, "name"):
            class_name = f"{self.name}"
        text_surface = pygame.font.SysFont(None, 24).render(class_name, True, (255, 255, 255))

        # Create a new surface for the object
        obj_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.rect(obj_surface, self.dummy_render_color, pygame.Rect(0, 0, tile_size, tile_size))
        obj_surface.blit(text_surface, (0, 0))

        # Merge obj_surface onto the input surface at the correct position
        surface.blit(obj_surface, (screen_x, screen_y))

        self.needs_redraw = False
        return surface