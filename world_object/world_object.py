import pygame
import itertools

class WorldObject:
    def __init__(self, x:float, y:float):
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
