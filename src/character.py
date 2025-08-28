import math
import random
import pygame

class Character:
    def __init__(self, x, y, speed=100, blocked_terrains=None):
        """
        Base class for any character.
        x, y: pixel coordinates
        speed: pixels per second
        blocked_terrains: list of terrain names this character cannot enter
        """
        self.x = x
        self.y = y
        self.speed = speed
        self.path = []  # list of (px, py) positions to follow
        self.blocked_terrains = blocked_terrains or []

    def set_path(self, path):
        """Assign a path (list of pixel positions) for movement"""
        self.path = path

    def update(self, dt):
        """Move along the path by speed * dt"""
        if self.path:
            target_x, target_y = self.path[0]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy)
            if distance == 0:
                self.path.pop(0)
                return
            step = self.speed * dt
            if step >= distance:
                self.x, self.y = target_x, target_y
                self.path.pop(0)
            else:
                self.x += dx / distance * step
                self.y += dy / distance * step

    def draw(self, surface, color=(255, 0, 0), size=20):
        """Draw character as a rectangle"""
        pygame.draw.rect(surface, color,
                         pygame.Rect(int(self.x - size / 2),
                                     int(self.y - size / 2),
                                     size, size))

class RandomCharacter(Character):
    def __init__(self, x, y, speed=100, blocked_terrains=None):
        super().__init__(x, y, speed, blocked_terrains)

    def move_randomly(self, grid, dt, tile_size):
        """
        Move randomly to adjacent tiles not blocked for this character.
        grid: 2D list of Tile objects
        dt: delta time
        tile_size: size of each tile in pixels
        """
        # If currently following a path, just update
        if self.path:
            self.update(dt)
            return

        # Possible directions (8 neighbors)
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]
        random.shuffle(directions)

        gx = int(self.x // tile_size)
        gy = int(self.y // tile_size)
        height = len(grid)
        width = len(grid[0])

        for dx, dy in directions:
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < width and 0 <= ny < height:
                tile = grid[ny][nx]
                # Avoid blocked terrains or tiles with resources
                if tile.terrain.name not in self.blocked_terrains and tile.resource is None:
                    target_x = nx * tile_size + tile_size/2
                    target_y = ny * tile_size + tile_size/2
                    self.set_path([(target_x, target_y)])
                    break

        # Move along the path
        self.update(dt)
