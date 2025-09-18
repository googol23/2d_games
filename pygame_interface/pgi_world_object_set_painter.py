import pygame
from camera import Camera
from manager import Manager
from .pgi_world_object_painter import PGIWorldObjectPainter

class PGIWorldObjectSetPainter(pygame.sprite.Group):
    """
    World Object Painter using sprites with efficient culling.
    Draws agents and static objects from the Manager.
    """

    def __init__(self, manager: Manager):
        super().__init__()
        self.manager = manager
        self.camera = Camera.get_instance()
        self.object_sprites: dict[int, PGIWorldObjectPainter] = {}  # obj.id -> sprite

        self._visible_objects = []
        self._last_camera_state = (None, None, None)  # x, y, tile_size

    def _compute_visible_objects(self):
        """Update the list of visible objects based on camera position."""
        cam = self.camera
        if (cam.x, cam.y, cam.tile_size) == self._last_camera_state:
            return  # no change

        self._visible_objects.clear()

        # Retrieve dynamic agents
        for agent in self.manager.get_agents():
            if cam.in_view(agent.x, agent.y):
                self._visible_objects.append(agent)

        # Retrieve static objects
        for obj in self.manager.static_objects:
            if cam.in_view(obj.x, obj.y):
                self._visible_objects.append(obj)

        self._last_camera_state = (cam.x, cam.y, cam.tile_size)

    def update(self):
        """Update visible PGIWorldObjectPainter sprites and their positions/images."""
        self._compute_visible_objects()
        tile_size = self.camera.tile_size

        for obj in self._visible_objects:
            key = id(obj)
            if key not in self.object_sprites:
                sprite = PGIWorldObjectPainter(obj, self.manager)
                sprite.update_image(tile_size)
                sprite.update_position(self.camera)
                self.object_sprites[key] = sprite
                super().add(sprite)
            else:
                sprite = self.object_sprites[key]
                sprite.update_image(tile_size)
                sprite.update_position(self.camera)

    def draw(self, surface: pygame.Surface):
        """Draw only visible object sprites."""
        visible_sprites = [self.object_sprites[id(obj)] for obj in self._visible_objects]
        pygame.sprite.Group(visible_sprites).draw(surface)

    def reset(self):
        """Call this when agents or static objects change."""
        self.object_sprites.clear()
        self._last_camera_state = (None, None, None)
        self._visible_objects.clear()
