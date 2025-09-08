import controls
class Camera:
    def __init__(self, x, y, width, height, tile_size):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.tile_size = tile_size

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.x) * self.tile_size
        screen_y = (world_y - self.y) * self.tile_size
        return screen_x, screen_y

    def in_view(self, world_x, world_y):
        """Check if object is inside camera view (world coordinates)"""
        return (
            world_x + 1 > self.x and
            world_x < self.x + self.width / self.tile_size and
            world_y + 1 > self.y and
            world_y < self.y + self.height / self.tile_size
        )

    def edge_pan(self, mx, my, factor=0.1):
        """
        Pan the camera when mouse is near edges.
        Pan speed is proportional to the number of tiles visible.

        :param mx: mouse x position
        :param my: mouse y position
        :param factor: fraction of visible tiles to move per frame (e.g., 0.1 = 10%)
        """
        # Compute number of tiles visible horizontally and vertically
        tiles_x = self.width / self.tile_size
        tiles_y = self.height / self.tile_size

        # Pan speed = fraction of visible tiles
        speed_x = tiles_x * factor
        speed_y = tiles_y * factor

        # Horizontal movement
        self.x += speed_x if mx > self.width - controls.PAN_EDGE_SIZE else -speed_x if mx < controls.PAN_EDGE_SIZE else 0
        # Vertical movement
        self.y += speed_y if my > self.height - controls.PAN_EDGE_SIZE else -speed_y if my < controls.PAN_EDGE_SIZE else 0
