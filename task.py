import pygame

ROOT_KEYS = {
    pygame.K_g: "Gathering",
    pygame.K_b: "Building",
    pygame.K_h: "Hunting",
    pygame.K_c: "Crafting",
}

TASK_TREE = {
    "Gathering": {
        "keys": {
            pygame.K_s: "Stone",
            pygame.K_b: "Berries",
            pygame.K_w: "Wood"
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