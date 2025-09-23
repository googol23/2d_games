
import numpy as np

from typing_extensions import Self
from .world_generator import WorldGen
from .tile import Tile

import logging
logger = logging.getLogger(__name__)

class World:
    """
    Represents the game world
    """
    def __init__(self, gen: WorldGen):
        self.gen:WorldGen = gen


        logger.info("Creating new World ...")
        logger.info(" ... pre-allocating world tiles")

        self.tiles: np.ndarray[Tile] | None = None
        self.elements: np.ndarray | None = None
        self.topology: np.ndarray[np.float16] | None = None
        self.obstacle: np.ndarray[np.bool_] | None = None

    @property
    def width(self)->int:
        return self.gen.config.WIDTH

    @property
    def height(self)->int:
        return self.gen.config.HEIGHT

    @property
    def topo_width(self)->int:
        return self.gen.config.WIDTH * self.gen.config.TILE_SUBDIVISIONS

    @property
    def topo_height(self)->int:
        return self.gen.config.HEIGHT * self.gen.config.TILE_SUBDIVISIONS

    @property
    def scale(self)->float:
        return self.gen.config.SCALE

    def get_tile(self, x: int, y: int) -> Tile:
        """Retrieves a tile at the given coordinates."""
        return self.tiles[y,x]

    def set_tile(self, x: int, y: int, tile: Tile):
        """Sets a tile at the given coordinates."""
        self.tiles[y,x] = tile

    def __str__(self):
        return f"World: size_x = {self.size_x}, size_y = {self.size_y}"

    def generate(self) -> Self:
        self.tiles, self.elements, self.topology, self.obstacle = self.gen.generate()