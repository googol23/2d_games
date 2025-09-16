import pygame
from camera import Camera
from controls import CAMERA_KEYS, ZOOM_KEYS

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

        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:
                self.camera.zoom(event.y)
            print(event)


        # Handle edge-pan
        mx, my = pygame.mouse.get_pos()
        screen_width, screen_height = pygame.display.get_surface().get_size()

        if mx < self.camera.config.PAN_EDGE_SIZE:
            self.camera.move(-1, 0)
        elif mx > screen_width - self.camera.config.PAN_EDGE_SIZE:
            self.camera.move(1, 0)
        if my < self.camera.config.PAN_EDGE_SIZE:
            self.camera.move(0, -1)
        elif my > screen_height - self.camera.config.PAN_EDGE_SIZE:
            self.camera.move(0, 1)
