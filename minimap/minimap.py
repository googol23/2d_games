from world import World
from camera import Camera
import pygame
from typing_extensions import Self


class MiniMap:
    _self: Self | None = None

    def __new__(cls, *args, **kwargs):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self, size=200, position=(0,0)):
        self.size = size
        self.position = position
        self.surface = pygame.Surface((size, size))
        self.needs_redraw = True

    @classmethod
    def get_instance(cls):
        if cls._self is None:
            raise RuntimeError("MiniMap not created yet")
        return cls._self

    def render(self, surface:pygame.Surface | None = None):
        world = World.get_instance()
        camera = Camera.get_instance()

        if self.needs_redraw:
            tile_w = self.size / world.world_size_x
            tile_h = self.size / world.world_size_y

            for y in range(world.world_size_y):
                for x in range(world.world_size_x):
                    tile = world.get_tile(x, y)
                    color = tile.terrain.color if tile.terrain else (87, 87, 87)
                    rect = pygame.Rect(x * tile_w, y * tile_h, tile_w + 1, tile_h + 1)
                    self.surface.fill(color, rect)

            self.needs_redraw = False

        # Copy cached minimap and overlay camera rect
        frame_surface = self.surface.copy()

        scale_x = self.size / world.world_size_x
        scale_y = self.size / world.world_size_y
        cam_rect = pygame.Rect(
            camera.x * scale_x,
            camera.y * scale_y,
            camera.width_tls * scale_x,
            camera.height_tls * scale_y,
        )
        pygame.draw.rect(frame_surface, (255, 0, 0), cam_rect, 2)

        # Border
        pygame.draw.rect(frame_surface, (0, 0, 0), frame_surface.get_rect(), 2)

        return frame_surface


    def handle_click(self, mouse_pos):
        world = World.get_instance()
        camera = Camera.get_instance()
        mx, my = mouse_pos
        px, py = self.position
        if px <= mx < px + self.size and py <= my < py + self.size:
            rel_x = mx - px
            rel_y = my - py

            # Map to world tiles
            world_x = rel_x / self.size * world.world_size_x
            world_y = rel_y / self.size * world.world_size_y

            # Convert to camera coordinates in pixels
            camera.x = max(0, min((world_x - camera.width_tls / 2) * camera.tile_size,
                                       world.world_size_x * camera.tile_size - camera.width_pxl))
            camera.y = max(0, min((world_y - camera.height_tls / 2) * camera.tile_size,
                                       world.world_size_y * camera.tile_size - camera.height_pxl))
