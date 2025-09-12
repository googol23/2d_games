from world_object import WorldObject
from world import World
from commands import Command, MoveCommand
from collections import deque
from enum import Enum
from world import Tile

class MoveMode(Enum):
    SWIM:float = 0.2
    CLIMB:float = 0.2
    WALK:float = 1
    RUN:float = 3


class Agent(WorldObject):
    class State(Enum):
        IDLE = 0
        MOVING = 1
        BUSY = 2

    def __init__(self, x: float = 0, y: float = 0, base_speed: float = 1.0):
        super().__init__(x, y)
        self.path:list[tuple[float,float]] = []
        self.commands:deque = deque()

        self.base_speed:float = base_speed      # meters per second
        self.move_mode = MoveMode.WALK

        self.world: World | None = World.get_instance()
    @property
    def state(self) -> State:
        if len(self.commands) == 0:
            return self.State.IDLE
        elif isinstance(self.commands[0], MoveCommand):
            return self.State.MOVING
        else:
            return self.State.BUSY

    @property
    def speed(self)->float:
        mode = self.move_mode
        # Override mode if in water or climbing terrain
        if self.world and self.world.get_tile(int(self.x), int(self.y)).is_water:
            mode = MoveMode.SWIM
        # TODO extend for climbing type terrains
        return self.base_speed * mode.value

    def set_move_mode(self, mode:MoveMode = MoveMode.WALK):
        self.move_mode = mode

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
