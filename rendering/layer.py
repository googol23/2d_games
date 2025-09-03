import pygame
from .camera import Camera

class Layer:
    def __init__(self, width, height, transparent=False):
        flags = pygame.SRCALPHA if transparent else 0
        self.surface = pygame.Surface((width, height), flags)
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)
        obj.needs_redraw = True

    def draw(self, camera: Camera):
        for obj in self.objects:
            if obj.needs_redraw:
                obj.render(self.surface, camera)
