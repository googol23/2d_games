import pygame
from camera import Camera
from world import World

class Layer:
    def __init__(self, width, height, transparent=False):
        flags = pygame.SRCALPHA if transparent else 0
        self.surface = pygame.Surface((width, height), flags)
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)

    def clear(self):
        """Clear the layer each frame before redrawing"""
        self.surface.fill((0, 0, 0, 0))

    def draw(self, camera:Camera):
        """Redraw all objects that are inside the camera view"""
        self.clear()

    def draw(self, camera: Camera):
        """Draw all objects that are inside the camera view (by x,y only)"""
        self.clear()

        for obj in self.objects:
            if isinstance(obj,World):
                obj.render(self.surface, camera)
            elif camera.in_view(obj.x, obj.y):
                # Cull: skip if outside the screen bounds
                obj.render(self.surface, camera)
