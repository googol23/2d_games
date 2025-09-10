from world_object import WorldObject
from commands import Command
from collections import deque

class Agent(WorldObject):
    def __init__(self, x: float = 0, y: float = 0, speed: float = 1.0):
        super().__init__(x, y)
        self.path:list = []
        self.speed:float = speed      # meters per second
        self.moving:bool = False

        self.state = "Idle"
        self.commands:deque = deque()   # fixed typo

    def assign_command(self, command: Command):
        self.commands.append(command)

    def set_path(self, path):
        """Set a new path for the agent to follow (list of (x, y) meters)."""
        self.path = path
        self.needs_redraw = True

    def update(self, dt: float = 0.0):
        if self.commands:
            current = self.commands[0]
            done = current.execute(self, dt)
            if done:
                self.commands.popleft()
        else:
            self.state = "Idle"
