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
        self.world:World = World.get_instance()
        self.camera:Camera = Camera.get_instance()

    @classmethod
    def get_instance(cls):
        if cls._self is None:
            raise RuntimeError("MiniMap not created yet")
        return cls._self

    def draw(self, surface:pygame.Surface | None = None):

        if self.needs_redraw:
            tile_w = self.size / self.world.size_x
            tile_h = self.size / self.world.size_y

            for y in range(self.world.size_y):
                for x in range(self.world.size_x):
                    tile = self.world.get_tile(x, y)
                    color = tile.terrain.color if tile.terrain else (87, 87, 87)
                    rect = pygame.Rect(x * tile_w, y * tile_h, tile_w + 1, tile_h + 1)
                    self.surface.fill(color, rect)

            self.needs_redraw = False

        scale_x = self.size / self.world.size_x
        scale_y = self.size / self.world.size_y
        cam_rect = pygame.Rect(
            self.camera.x * scale_x,
            self.camera.y * scale_y,
            self.camera.width_tls * scale_x,
            self.camera.height_tls * scale_y,
        )

        # Copy cached minimap and overlay camera rect
        frame_surface = self.surface.copy()
        pygame.draw.rect(frame_surface, (255, 0, 0), cam_rect, 5)
        pygame.draw.rect(frame_surface, (0, 0, 0), frame_surface.get_rect(), 2)  # border
        surface.blit(frame_surface, self.position)


    def handle_click(self, mouse_pos):
        mx, my = mouse_pos
        px, py = self.position
        if px <= mx < px + self.size and py <= my < py + self.size:
            rel_x = mx - px
            rel_y = my - py

            # Map to world tiles
            world_x = rel_x / self.size * self.world.size_x
            world_y = rel_y / self.size * self.world.size_y

            self.camera.x = max(0, min(world_x - self.camera.width_tls / 2, self.world.size_x - self.camera.width_tls))
            self.camera.y = max(0, min(world_y - self.camera.height_tls / 2, self.world.size_y - self.camera.height_tls))

