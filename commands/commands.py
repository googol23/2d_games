from abc import ABC, abstractmethod
from collections import deque
import math

class Command(ABC):
    @abstractmethod
    def execute(self, agent, dt: float = 0.0):
        """
        Execute a step of the command on the given agent.
        Return True when finished, False otherwise.
        """
        pass

class MoveCommand(Command):
    def __init__(self, path):
        # path is a list of waypoints [(x, y), ...] in meters
        self.path = deque(path)

    def execute(self, agent, dt: float = 0.0):
        if not self.path:
            return True

        target_x, target_y = self.path[0]
        dx, dy = target_x - agent.x, target_y - agent.y
        dist = math.hypot(dx, dy)

        # meters to move this update
        step = agent.speed * dt

        if dist <= step:
            # reached waypoint
            agent.x, agent.y = target_x, target_y
            self.path.popleft()
        else:
            # move fractionally toward target
            agent.x += dx / dist * step
            agent.y += dy / dist * step

        agent.state = "Moving"
        return False

class IdleCommand(Command):
    def execute(self, agent, dt: float = 0.0):
        agent.state = "Idle"
        return True
