import pygame
from camera.camera import Camera

class PGITilePainter:
    """
    Handles rendering a single Tile.
    Maintains a cached surface for the current view mode.
    """
    def __init__(self, tile):
        self.tile = tile
        self.camera = Camera.get_instance()
        self.cached_tile_size = None
        self.sprite_surface = None  # Single active surface
        self.cached_view = None     # "iso" or "top"

    def _create_surface(self, iso: bool):
        """
        Pre-render the tile surface for the requested view.
        """
        view_mode = "iso" if iso else "top"
        tile_size = self.camera.tile_size

        if self.cached_tile_size == tile_size and self.cached_view == view_mode and self.sprite_surface:
            return  # already up-to-date

        self.cached_tile_size = tile_size
        self.cached_view = view_mode

        if iso:
            width = tile_size * 2
            height = tile_size
        else:
            width = height = tile_size

        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        self._draw_tile(surf, width, height, iso)
        self.sprite_surface = surf

    def _draw_tile(self, surf: pygame.Surface, width: int, height: int, iso: bool):
        """Draw the tile shape according to the view mode."""
        if self.tile.terrain:
            if getattr(self.tile.terrain, "texture", None):
                # Assume texture already matches the view, just scale
                scaled = pygame.transform.scale(self.tile.terrain.texture, (width, height))
                surf.blit(scaled, (0, 0))
            elif hasattr(self.tile.terrain, "color"):
                color = self.tile.terrain.color
                if iso:
                    # Draw a diamond for iso
                    points = [
                        (width//2, 0),
                        (width, height//2),
                        (width//2, height),
                        (0, height//2)
                    ]
                    pygame.draw.polygon(surf, color, points)
                else:
                    # Draw square for top-down
                    pygame.draw.rect(surf, color, pygame.Rect(0, 0, width, height))
            else:
                # Default fallback color
                pygame.draw.rect(surf, (87, 87, 87), pygame.Rect(0, 0, width, height))
        else:
            # Default fallback if no terrain
            if iso:
                points = [
                    (width//2, 0),
                    (width, height//2),
                    (width//2, height),
                    (0, height//2)
                ]
                pygame.draw.polygon(surf, (87, 87, 87), points)
            else:
                pygame.draw.rect(surf, (87, 87, 87), pygame.Rect(0, 0, width, height))

    def update_iso(self, surface: pygame.Surface, world_x: int, world_y: int):
        self._create_surface(iso=True)
        sx, sy = self.camera.world_to_screen_iso(world_x, world_y)
        surface.blit(self.sprite_surface, (sx, sy))

    def update_top(self, surface: pygame.Surface, world_x: int, world_y: int):
        self._create_surface(iso=False)
        sx, sy = self.camera.world_to_screen(world_x, world_y)
        surface.blit(self.sprite_surface, (sx, sy))

    def invalidate_cache(self):
        self.cached_tile_size = None
        self.cached_view = None
