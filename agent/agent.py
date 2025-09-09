from world_object import WorldObject

class Agent(WorldObject):
    def __init__(self, x:float = 0, y:float = 0, speed:float=1.0):
        super().__init__(x, y)
        self.path = []          # List of (x, y) positions to move along
        self.speed = speed      # Tiles per update
        self.moving = False

    def set_path(self, path):
        """Set a new path for the agent to follow."""
        self.path = path
        self.needs_redraw = True

    def update(self, dt: float = 0):
        """Move along the path using coordinate-based movement provided inside self.path."""
        if not self.moving or not self.path:
            return

        target_x, target_y = self.path[0]
        dx = target_x - self.x
        dy = target_y - self.y
        ds = (dx ** 2 + dy ** 2) ** 0.5

        if ds == 0:
            # Already at the target
            self.path.pop(0)
            if not self.path:
                self.moving = False
            return

        # Move along the direction vector
        step = self.speed * dt
        if ds <= step:
            # Reached the target
            self.x, self.y = target_x, target_y
            self.path.pop(0)
            if not self.path:
                self.moving = False
        else:
            # Move proportionally along x and y
            self.x += dx / ds * step
            self.y += dy / ds * step

        self.needs_redraw = True
