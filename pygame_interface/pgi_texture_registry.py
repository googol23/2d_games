import pygame
from itertools import count
from pathlib import Path
from camera import Camera

# Global cache: (texture_id, tile_size) -> Surface
SURFACE_CACHE: dict[tuple[int, int], pygame.Surface] = {}

# Unique texture IDs
from itertools import count
TEXTURE_REGISTRY: dict[str, int] = {}
_TEXTURE_ID_COUNTER = count(1)

def register_texture(path: str) -> int:
    """Assign a unique integer ID to a texture path."""
    path = str(Path(path))
    if path in TEXTURE_REGISTRY:
        return TEXTURE_REGISTRY[path]
    tex_id = next(_TEXTURE_ID_COUNTER)
    TEXTURE_REGISTRY[path] = tex_id
    return tex_id

def preload_texture_zoom_levels(path: str) -> int:
    """
    Precompute and cache scaled surfaces for all zoom steps based on the Camera.
    """
    camera = Camera.get_instance()
    tex_id = register_texture(path)
    original = pygame.image.load(str(path)).convert_alpha()
    original.set_colorkey((255, 255, 55))

    min_tile = camera.config.MIN_TILE_SIZE
    max_tile = camera.config.MAX_TILE_SIZE
    step = camera.config.ZOOM_STEP

    for ts in range(min_tile, max_tile + 1, step):
        if (tex_id, ts) not in SURFACE_CACHE:
            scaled = pygame.transform.smoothscale(original, (ts, ts))
            SURFACE_CACHE[(tex_id, ts)] = scaled

    return tex_id
