import pygame
from rendering import Camera
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
        if not camera.in_view(self.x, self.y):
            return  # Skip if off-screen

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        tile_size = camera.tile_size

        pygame.draw.rect(surface, self.dummy_render_color, pygame.Rect(screen_x, screen_y, tile_size, tile_size))

        self.needs_redraw = False