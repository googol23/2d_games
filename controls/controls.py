import pygame

# Movement keys mapped to (dx, dy)
MOVEMENT_KEYS = {
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
}

# Camera movement keys (WASD)
CAMERA_KEYS = {
    pygame.K_a: (-1, 0),
    pygame.K_d: (1, 0),
    pygame.K_w: (0, -1),
    pygame.K_s: (0, 1),
}

ZOOM_KEYS = {
    pygame.K_KP_PLUS: 1,
    pygame.K_KP_MINUS:-1
}


# Other actions
OVERLAY_GRID_KEY = pygame.K_g
TOGGLE_OVERLAY_KEY = pygame.K_F1
REGENERATE_WORLD_KEY = pygame.K_KP_ENTER

PAUSE_GAME_KEY = pygame.K_F10