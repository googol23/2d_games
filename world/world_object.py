class WorldObject:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    @property
    def tile(self):
        return int(self.x), int(self.y)
