from world import World
import pygame

from terrain import TERRAIN_DATA
from camera import Camera

import logging
logger = logging.getLogger(__name__)


class PGIWorldPainter:
    def __init__(self):
        self.world = World.get_instance()

    def render(self, surface: pygame.Surface):
        """
        Renders the visible portion of the world, making it efficient for a dynamic
        camera and world.
        """
        camera = Camera.get_instance()
        tile_size = camera.tile_size

         # Fill background so out-of-bounds areas don't leave artifacts
        surface.fill((0, 0, 0))  # or ocean blue, or whatever makes sense

        # Cull: compute visible bounds once
        start_x = max(int(camera.x), 0)
        end_x   = min(int(camera.x + camera.width_tls + 1), self.world.world_size_x)
        start_y = max(int(camera.y), 0)
        end_y   = min(int(camera.y + camera.height_tls + 1), self.world.world_size_y)

        # Loop only over visible tiles
        for y in range(start_y, end_y):
            row_offset = y * self.world.world_size_x
            screen_y = round(y * tile_size - camera.y * tile_size)
            for x in range(start_x, end_x):
                tile = self.world.tiles[row_offset + x]
                screen_x = round(x * tile_size - camera.x * tile_size)

                if tile.terrain:
                    if tile.terrain.texture:
                        surface.blit(
                            pygame.transform.scale(tile.terrain.texture, (tile_size, tile_size)),
                            (screen_x, screen_y),
                        )
                    else:
                        pygame.draw.rect(
                            surface,
                            tile.terrain.color,
                            pygame.Rect(screen_x, screen_y, tile_size, tile_size),
                        )
                else:
                    pygame.draw.rect(
                        surface,
                        (87, 87, 87),
                        pygame.Rect(screen_x, screen_y, tile_size, tile_size),
                    )