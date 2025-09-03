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
