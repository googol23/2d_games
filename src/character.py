import math
import random
import pygame

class Character:
    def __init__(self, x=0, y=0, speed=5, blocked_terrains=None):
        """
        Base class for any character.
        x, y: tile coordinates (map units)
        speed: tiles per second
        blocked_terrains: list of terrain names this character cannot enter
        """
        self.x = x
        self.y = y
        self.speed = speed
        self.path = []  # list of (tile_x, tile_y) positions
        self.blocked_terrains = blocked_terrains or []

    def set_path(self, path):
        """Assign a path (list of tile positions) for movement"""
        self.path = path

    def update(self, dt):
        """Move along the path by speed * dt (in tiles)"""
        if not self.path:
            return

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

    def draw(self, surface, tile_size, camera_x, camera_y, color=(255,0,0)):
        """Draw character relative to camera"""
        screen_x = self.x * tile_size - camera_x
        screen_y = self.y * tile_size - camera_y
        pygame.draw.rect(surface, color,
                         pygame.Rect(int(screen_x - tile_size/2),
                                     int(screen_y - tile_size/2),
                                     tile_size, tile_size))

class RandomCharacter(Character):
    def __init__(self, x=0, y=0, speed=5, blocked_terrains=None):
        super().__init__(x, y, speed, blocked_terrains)

    def move_randomly(self, grid, dt):
        """
        Move randomly to adjacent tiles not blocked.
        grid: 2D list of Tile objects
        dt: delta time
        """
        # If currently following a path, just update
        if self.path:
            self.update(dt)
            return

        directions = [(0,-1),(0,1),(-1,0),(1,0),
                      (-1,-1),(-1,1),(1,-1),(1,1)]
        random.shuffle(directions)

        gx = int(self.x)
        gy = int(self.y)
        height = len(grid)
        width = len(grid[0])

        for dx, dy in directions:
            nx, ny = gx + dx, gy + dy
            if 0 <= nx < width and 0 <= ny < height:
                tile = grid[ny][nx]
                if tile.terrain.name not in self.blocked_terrains:
                    self.set_path([(nx+0.5, ny+0.5)])  # move to center of tile
                    break

        self.update(dt)
