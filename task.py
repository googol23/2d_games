import pygame


TASK_TREE = {
    "Gathering": {
        "keys": {
            pygame.K_s: "stone",
            pygame.K_b: "berries",
            pygame.K_w: "wood"
        },
        "next": "item"
    },
    "Building": {
        "keys": {pygame.K_s: "shelter", pygame.K_a: "wall"},
        "next": "item"
    }
}

LOCATIONS = {
    "keys": {pygame.K_h: "here", pygame.K_m: "mouse"},
}