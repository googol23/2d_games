import pygame

from manager import Manager
from camera import Camera
from agent import Agent, MoveMode
from pathfinder import Pathfinder
import commands

import logging
logger = logging.getLogger("pgi")

DOUBLE_CLICK_TIME = 300  # ms between clicks

last_right_click_time = 0

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

                time_now = pygame.time.get_ticks()
                global last_right_click_time
                for agent_id in self.manager.selection:
                    agent = self.manager.agents[agent_id]
                    """
                    If current command is MoveCommand and time difference to last right click
                    is within DOUBLE_CLICK_TIME window, use right click as agent speed modifier
                    """
                    if time_now - last_right_click_time <= DOUBLE_CLICK_TIME:
                        agent.move_mode(MoveMode.RUN)
                    else:
                        # Find path
                        path = Pathfinder(self.manager.world).find_path(start=(agent.x,agent.y),goal=world_pos)
                        agent.commands.clear()
                        agent.move_mode(MoveMode.WALK)
                        agent.assign_command(commands.MoveCommand(path))
                        logger.debug(f"command assigned to {agent_id}: MoveCommnad, from {(agent.x,agent.y)} to {world_pos}")

                last_right_click_time = time_now
            # --- Esc: clear selection
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.manager.selection.clear()
                logger.debug("Selection cleared with Esc")