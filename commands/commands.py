from abc import ABC, abstractmethod
from collections import deque
import math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from agent import Agent


class Command(ABC):
    @abstractmethod
    def execute(self, agent, dt: float = 0.0) -> bool:
        """
        Execute a step of the command on the given agent.
        Return True when finished, False otherwise.
        """
        ...

class MoveCommand(Command):
    def __init__(self, path):
        # path is a list of waypoints [(x, y), ...] in meters
        self.path = deque(path)

    def execute(self, agent, dt: float = 0.0) -> bool:
        if not self.path:
            return True


        target_x, target_y = self.path[0]
        dx, dy = target_x - agent.x, target_y - agent.y
        dist = math.hypot(dx, dy)

        # meters to move this update
        ds = agent.speed * dt

        from character import Human
        if isinstance(agent, Human):
            agent.metric.distance += ds
            agent.metric.steps += 1

        if dist <= ds:
            # reached waypoint
            agent.x, agent.y = target_x, target_y
            self.path.popleft()
        else:
            # move fractionally toward target
            agent.x += dx / dist * ds
            agent.y += dy / dist * ds

        return False

class IdleCommand(Command):
    def execute(self, agent, dt: float = 0.0):
        agent.state = agent.State.IDLE
        return True
