from world_object import WorldObject
from world import World
from commands import Command, MoveCommand
from collections import deque
from enum import Enum
from world import Tile

class MoveMode(Enum):
    WALK: int = 1
    RUN:  int = 2
    SWIM: int = 3
    CLIMB:int = 4


class Agent(WorldObject):
    class State(Enum):
        IDLE = 0
        MOVING = 1
        BUSY = 2

    # Class-level default
    NATURAL_MOVE_MODE: MoveMode = MoveMode.WALK
    MOVE_MULTIPLIERS: dict[MoveMode, float] = {
        MoveMode.WALK: 1.0,
        MoveMode.RUN: 1.0,
        MoveMode.SWIM: 1.0,
        MoveMode.CLIMB: 1.0,
    }

    def __init__(self, x: float = 0, y: float = 0, base_speed: float = 1.0):
        super().__init__(x, y)
        self.path:list[tuple[float,float]] = []
        self.commands:deque = deque()

        self.base_speed:float = base_speed
        self.move_mode = self.NATURAL_MOVE_MODE
        self.move_mode_factor:dict[MoveMode,float] = self.MOVE_MULTIPLIERS

        self.world: World | None = World.get_instance()

    @property
    def natural_move_mode(self) -> MoveMode:
        return self.NATURAL_MOVE_MODE

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
        return self.base_speed * self.move_mode_factor[mode]

    def speed_at(self, x:int, y:int) -> float:
        mode = self.natural_move_mode
        if self.world and self.world.get_tile(x, y).is_water:
            mode = MoveMode.SWIM
        # TODO extend for climbing type terrains
        return self.base_speed * self.move_mode_factor[mode]

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
