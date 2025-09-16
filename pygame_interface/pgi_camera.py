import pygame
from camera import Camera
from controls import CAMERA_KEYS, ZOOM_KEYS

class PGICameraControl:
    def __init__(self):
        self.camera: Camera = Camera.get_instance()

    def handle_actions(self, events: list[pygame.event.Event] | None = None, keys:pygame.key.ScancodeWrapper | None = None, mouse_pos:tuple[int,int] | None = None):
        """
        Handle pygame events to control camera.

        """
        if keys:
            # Handle keyboard movements
            for key, (dx, dy) in CAMERA_KEYS.items():
                if keys[key]:
                    self.camera.move(dx, dy)

            # Handle zoom
            for key, direction in ZOOM_KEYS.items():
                if keys[key]:
                    self.camera.zoom(direction)

            # TODO implement scroll ZOOM

        # Handle edge-pan
        if mouse_pos:
            mx, my = mouse_pos
            screen_width, screen_height = self.camera.width_pxl, self.camera.height_pxl

            if mx < self.camera.config.PAN_EDGE_SIZE:
                self.camera.move(-1, 0)
            elif mx > screen_width - self.camera.config.PAN_EDGE_SIZE:
                self.camera.move(1, 0)
            if my < self.camera.config.PAN_EDGE_SIZE:
                self.camera.move(0, -1)
            elif my > screen_height - self.camera.config.PAN_EDGE_SIZE:
                self.camera.move(0, 1)
