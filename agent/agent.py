from world_object import WorldObject
from commands import Command
from collections import deque
from enum import Enum

class MoveMode(Enum):
    SWIM:float = 0.2
    CLIMB:float = 0.2
    WALK:float = 1
    RUN:float = 2

class Agent(WorldObject):
    def __init__(self, x: float = 0, y: float = 0, speed: float = 1.0):
        super().__init__(x, y)
        self.path:list[tuple[float,float]] = []
        self.speed:float = speed           # meters per second
        self.base_speed:float = speed      # meters per second
        self.moving:bool = False

        self.state = "Idle"
        self.commands:deque = deque()   # fixed typo

    def get_speed(self):
        return self.speed

    def move_mode(self, mode:MoveMode = MoveMode.WALK):
        self.speed = self.base_speed * mode.value

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
