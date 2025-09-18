from world_object import WorldObject
import numpy as np

class WorldElements:
    def __init__(self, world_size_x:int, world_size_y:int, subdivisions:int = 10):
        """ This represent a finder grid of the World by partitioning each tile in subdivisions """
        self.size_x: int = world_size_x * subdivisions
        self.size_y: int = world_size_y * subdivisions
        self.subdivisions = subdivisions

        self.grid = np.full((self.size_x,self.size_y), -1, dtype=int) # 2D grid to store objects id that and block the cell(subtile)

    def __str__(self):
        return self.grid.__str__()

    def world_to_cell(self, x:float, y:float) -> tuple[int,int]:
        """Transform world coordinates into discrete grid coordinates."""
        cx = int(x * self.subdivisions)
        cy = int(y * self.subdivisions)
        return cx, cy

    def cell_to_world(self, cx:int, cy:int) -> tuple[int,int]:
        return cx/self.subdivisions, cy/self.subdivisions

    def insert(self, element:WorldObject):
        self.grid[*self.world_to_cell(element.x,element.y)] = element.id

    def remove(self, element:WorldObject):
        self.grid[*self.world_to_cell(element.x,element.y)] = -1


    def collides(self, element:WorldObject):
        return len(self.grid[self.world_to_cell(element.x,element.y)]) > 0

