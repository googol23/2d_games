import pygame
from camera import Camera
from world_object import WorldObject

class Layer:
    def __init__(self, width, height, transparent=False):
        self.camera = Camera.get_instance()
        flags = pygame.SRCALPHA if transparent else 0
        self.surface = pygame.Surface((self.camera.width_pxl, self.camera.height_pxl), flags)
        self.sprites = pygame.sprite.Group()
        self.objects = []

    def add_sprite(self, sprite: pygame.sprite):
        self.sprites.add(sprite)

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

    def clear(self):
        """Clear the layer each frame before redrawing"""
        self.surface.fill((0, 0, 0, 0))

    def draw(self):
        """Draw all objects that are inside the camera view (by x,y only)"""
        self.clear()

        for obj in self.objects:
            if isinstance(obj,WorldObject):
                if self.camera.in_view(obj.x, obj.y):
                    # Cull: skip if outside the screen bounds
                    obj.render(self.surface)
            else:
                obj.render(self.surface)

        self.sprites.update()
        self.sprites.draw(self.surface)
