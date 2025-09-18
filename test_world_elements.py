from world_elements import WorldElements
from world_object import WorldObject

import random

we = WorldElements(10,10,2)

for i in range (10):
    x = 10 * random.randint(0,1000) / 1000.
    y = 10 * random.randint(0,1000) / 1000.
    
    we.insert(WorldObject(x,y))
    

print(we)