import pygame

from manager import Manager
from camera import Camera
from agent import Agent
from pathfinder import Pathfinder
import commands

import logging
logger = logging.getLogger("pgi")

class PGIAgentControl:
    def __init__(self, manager: Manager, camera: Camera):
        self.manager: Manager = manager
        self.camera: Camera = camera

    def command_agents(self, events):
        if len(self.manager.selection) == 0:
            # No selected agents to command
            return

        # capture right click position
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
                mx,my = pygame.mouse.get_pos()
                world_pos = self.camera.screen_to_world(screen_x=mx,screen_y=my)
                for agent_id in self.manager.selection:
                    agent = self.manager.agents[agent_id]
                    logger.debug(f"command assigned to {agent_id}: MoveCommnad, from {(agent.x,agent.y)} to {world_pos}")
                    # Find path
                    path = Pathfinder(self.manager.world).find_path(start=(agent.x,agent.y),goal=world_pos)
                    agent.commands.clear()
                    agent.assign_command(commands.MoveCommand(path))