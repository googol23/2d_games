import pygame

class MiniMap:
    def __init__(self, world, camera, size=200, position=(0,0)):
        self.world = world
        self.camera = camera
        self.size = size
        self.position = position
        self.surface = pygame.Surface((size, size))
        self.needs_redraw = True

    def draw(self):
        if self.needs_redraw:
            self._render_minimap()
            self.needs_redraw = False

        frame_surface = self.surface.copy()
        self._draw_camera_rect(frame_surface)
        pygame.draw.rect(frame_surface, (0, 0, 0), frame_surface.get_rect(), 2)
        return frame_surface

    def _render_minimap(self):
        tile_w = self.size / self.world.world_size_x
        tile_h = self.size / self.world.world_size_y

        for y in range(self.world.world_size_y):
            for x in range(self.world.world_size_x):
                tile = self.world.get_tile(x, y)
                color = tile.terrain.color if tile.terrain else (87, 87, 87)
                rect = pygame.Rect(x * tile_w, y * tile_h, tile_w + 1, tile_h + 1)
                self.surface.fill(color, rect)

    def _draw_camera_rect(self, surface):
        # Each tile in pixels on minimap
        scale_x = self.size / self.world.world_size_x
        scale_y = self.size / self.world.world_size_y

        # Camera position in tiles
        cam_x_tiles = self.camera.x / self.camera.tile_size
        cam_y_tiles = self.camera.y / self.camera.tile_size
        cam_w_tiles = self.camera.width / self.camera.tile_size
        cam_h_tiles = self.camera.height / self.camera.tile_size

        cam_rect = pygame.Rect(
            cam_x_tiles * scale_x,
            cam_y_tiles * scale_y,
            cam_w_tiles * scale_x,
            cam_h_tiles * scale_y,
        )

        pygame.draw.rect(surface, (255, 0, 0), cam_rect, 2)

    def handle_click(self, mouse_pos):
        mx, my = mouse_pos
        px, py = self.position
        if px <= mx < px + self.size and py <= my < py + self.size:
            rel_x = mx - px
            rel_y = my - py

            # Map to world tiles
            world_x = rel_x / self.size * self.world.world_size_x
            world_y = rel_y / self.size * self.world.world_size_y

            # Convert to camera coordinates in pixels
            cam_w_tiles = self.camera.width / self.camera.tile_size
            cam_h_tiles = self.camera.height / self.camera.tile_size

            self.camera.x = max(0, min((world_x - cam_w_tiles / 2) * self.camera.tile_size,
                                       self.world.world_size_x * self.camera.tile_size - self.camera.width))
            self.camera.y = max(0, min((world_y - cam_h_tiles / 2) * self.camera.tile_size,
                                       self.world.world_size_y * self.camera.tile_size - self.camera.height))
