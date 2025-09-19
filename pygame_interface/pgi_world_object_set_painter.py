# pgi_world_object_set_painter.py
import pygame
from camera import Camera
from manager import Manager
from pygame.sprite import LayeredUpdates
from .pgi_world_object_painter import PGIWorldObjectPainter

import logging
logger = logging.getLogger("pgi")

class PGIWorldObjectSetPainter(LayeredUpdates):
    """
    Optimized Layered sprite group for world objects and agents.
    Only updates visible objects and caches images per zoom.
    """

    def __init__(self, manager: Manager):
        super().__init__()
        self.manager = manager
        self.camera = Camera.get_instance()
        self.object_sprites: dict[int, PGIWorldObjectPainter] = {}  # obj.id -> sprite
        self._last_camera_state = (None, None, None)

    def _compute_visible_objects(self):
        cam = self.camera
        if (cam.x, cam.y, cam.tile_size) == self._last_camera_state:
            return  # no change

        self._visible_objects = []

        # Static objects
        for obj in self.manager.static_objects:
            if cam.in_view(obj.x, obj.y):
                self._visible_objects.append(obj)

        self._last_camera_state = (cam.x, cam.y, cam.tile_size)

    def update(self):
        self._compute_visible_objects()
        cam = self.camera
        tile_size = cam.tile_size

        # Add or update sprites
        for obj in self._visible_objects:
            key = id(obj)
            if key not in self.object_sprites:
                sprite = PGIWorldObjectPainter(obj, self.manager)
                sprite.update_image(tile_size)
                sprite.update_position(cam)
                self.object_sprites[key] = sprite
                super().add(sprite)
            else:
                sprite = self.object_sprites[key]
                sprite.update_image(tile_size)
                sprite.update_position(cam)

        # Remove sprites that are no longer visible
        invisible_keys = set(self.object_sprites.keys()) - set(id(obj) for obj in self._visible_objects)
        for key in invisible_keys:
            super().remove(self.object_sprites[key])
            del self.object_sprites[key]

    def draw(self, surface: pygame.Surface):
        super().draw(surface)

    def reset(self):
        """Clear all cached sprites and reset camera state."""
        for sprite in self.object_sprites.values():
            super().remove(sprite)
        self.object_sprites.clear()
        self._last_camera_state = (None, None, None)