import pygame
from world_object import WorldObject
from camera import Camera

class WorldObjectSprite(pygame.sprite.Sprite):
    def __init__(self, world_obj):
        super().__init__()
        self.world_obj = world_obj
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)  # placeholder; size handled by camera
        self.rect = self.image.get_rect()

    def update(self):
        # Access the singleton camera
        camera = Camera.get_instance()

        # Update size based on current tile_size (zoom)
        tile_size = camera.tile_size
        self.image = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.world_obj.dummy_render_color, self.image.get_rect())

        # Draw the object’s name (optional)
        text_surface = pygame.font.SysFont(None, 24).render(
            getattr(self.world_obj, "name", type(self.world_obj).__name__), True, (255, 255, 255)
        )
        self.image.blit(text_surface, (0, 0))

        # Convert world coordinates to screen coordinates
        screen_x, screen_y = camera.world_to_screen(self.world_obj.x, self.world_obj.y)
        self.rect.topleft = (screen_x, screen_y)
