import pygame
from manager import Manager
from camera import Camera
from commands import MoveCommand

class PGIAgentPathPainter:
    def __init__(self, manager: Manager | None = None):
        self.manager: Manager = manager

    def render(self, surface):
        camera:Camera = Camera.get_instance()

        if not self.manager:
            return

        agents = self.manager.get_agents()
        for agent in agents:
            if len(agent.commands) == 0 or not isinstance(agent.commands[0], MoveCommand):
                continue

            # Convert world positions to screen positions
            points = [camera.world_to_screen(x, y) for (x, y) in agent.commands[0].path]

            if len(points) > 1:
                pygame.draw.lines(surface, (0, 0, 255), False, points, 2)
            elif len(points) > 0:
                # If only one point, draw a small dot
                px, py = points[0]
                pygame.draw.circle(surface, (0, 0, 255), (int(px), int(py)), 3)
