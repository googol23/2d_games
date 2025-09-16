import pygame
from functools import cached_property
from world import Tile  # your Tile class

class PGITilePainter(pygame.sprite.Sprite):
    """Sprite wrapper for a Tile with caching of rendered image."""

    def __init__(self, tile: Tile, x: int, y: int):
        super().__init__()
        self.tile = tile
        self.tile_x = x
        self.tile_y = y
        self._last_tile_size = None
        self._last_terrain = None
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def _render_surface(self, tile_size: int) -> pygame.Surface:
        """Render tile surface as a square, optionally draw terrain name."""
        surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        color = (0, 128, 0) if self.tile.terrain is None else getattr(self.tile.terrain, "color", (0,128,0))
        pygame.draw.rect(surf, color, surf.get_rect())

        return surf

    def update_image(self, tile_size: int):
        """Recompute image only if tile size or terrain changed."""
        terrain_id = id(self.tile.terrain) if self.tile.terrain else None
        if tile_size != self._last_tile_size or terrain_id != self._last_terrain:
            self.image = self._render_surface(tile_size)
            self.rect = self.image.get_rect()
            self._last_tile_size = tile_size
            self._last_terrain = terrain_id

    def update_position(self, camera):
        self.rect.topleft = tuple(map(int, camera.world_to_screen(self.tile_x, self.tile_y)))

