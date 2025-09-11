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

        # Use camera.width_tls and camera.height_tls for dimensions in tiles
        cam_rect = pygame.Rect(
            self.camera.x * scale_x,
            self.camera.y * scale_y,
            self.camera.width_tls * scale_x,
            self.camera.height_tls * scale_y,
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
            self.camera.x = max(0, min((world_x - self.camera.width_tls / 2) * self.camera.tile_size,
                                       self.world.world_size_x * self.camera.tile_size - self.camera.width_pxl))
            self.camera.y = max(0, min((world_y - self.camera.height_tls / 2) * self.camera.tile_size,
                                       self.world.world_size_y * self.camera.tile_size - self.camera.height_pxl))
