import pygame
from world import Tile  # your Tile class

# shared cache for all painters
_TEXTURE_CACHE = {}

class PGITilePainter(pygame.sprite.Sprite):
    """Sprite wrapper for a Tile with caching of rendered image."""

    def __init__(self, tile: Tile, x: int, y: int):
        super().__init__()
        self.tile:Tile = tile
        self.tile_x = x
        self.tile_y = y
        self._last_tile_size = None
        self._last_terrain = None
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def _get_texture(self, path: str, size: int) -> pygame.Surface | None:
        """Load and scale texture with caching."""
        key = (path, size)
        if key not in _TEXTURE_CACHE:
            try:
                tex = pygame.image.load(path).convert_alpha()
                tex = pygame.transform.smoothscale(tex, (size, size))
                _TEXTURE_CACHE[key] = tex
            except Exception as e:
                print(f"Failed to load texture {path}: {e}")
                return None
        return _TEXTURE_CACHE[key]

    def _render_surface(self, tile_size: int) -> pygame.Surface:
        """Render tile surface from texture if available, else solid color."""
        if self.tile.terrain:
            texture_path = getattr(self.tile.terrain, "texture", None)
            if texture_path:
                tex = self._get_texture(texture_path, tile_size)
                if tex:
                    return tex

        # fallback dummy color
        surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        color = getattr(self.tile.terrain, "color", (0, 128, 0))
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
