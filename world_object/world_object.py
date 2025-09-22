import pygame
import itertools

class WorldObject(pygame.sprite.Sprite):
    def __init__(self, x:float, y:float):
        super().__init__()
        self.id = itertools.count()
        self.x: float = x
        self.y: float = y
        self.needs_redraw = True
        self.dummy_render_color = (255,0,0)
        self.texture = None


    @property
    def tile(self):
        return int(self.x), int(self.y)

    def set_coordinates(self, x:float, y:float):
        self.x = x
        self.y = y

    def update(self, offset_x:int=0, offset_y:int=0, world_to_pixel=None):
        # Compute pixel position from world coordinates if world_to_pixel is provided
        if world_to_pixel is not None:
            px, py = world_to_pixel(self.x, self.y)
            self.rect.topleft = (px + offset_x, py + offset_y)
        else:
            # Fallback: keep current rect
            pass