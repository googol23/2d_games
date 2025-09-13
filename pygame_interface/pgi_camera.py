import pygame
from camera import Camera
from controls import CAMERA_KEYS, ZOOM_KEYS, PAN_EDGE_SIZE

class PGICameraControl:
    def __init__(self):
        self.camera: Camera = Camera.get_instance()

    def handle_actions(self):
        """
        Handle pygame events to control camera.

        """
        keys = pygame.key.get_pressed()

        # Handle keyboard movements
        for key, (dx, dy) in CAMERA_KEYS.items():
            if keys[key]:
                self.camera.move(dx, dy)

        # Handle zoom
        for key, direction in ZOOM_KEYS.items():
            if keys[key]:
                self.camera.zoom(direction)

        # Handle edge-pan
        mx, my = pygame.mouse.get_pos()
        screen_width, screen_height = pygame.display.get_surface().get_size()

        if mx < PAN_EDGE_SIZE:
            self.camera.move(-1, 0)
        elif mx > screen_width - PAN_EDGE_SIZE:
            self.camera.move(1, 0)
        if my < PAN_EDGE_SIZE:
            self.camera.move(0, -1)
        elif my > screen_height - PAN_EDGE_SIZE:
            self.camera.move(0, 1)
