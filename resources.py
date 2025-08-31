import logging
logger = logging.getLogger(__name__)

RESOURCE_DATA={}

class Resource:
    def __init__(self, name, color=None, texture=None, abundance=1):
        self.name = name
        self.color = color
        self.texture = texture
        self.abundance = abundance

    def __str__(self):
        return f"{self.name}: Abundance={self.abundance}, Color={self.color})\n"

    def __repr__(self):
        return self.__str__()

def load_resource_data(filename="resources_data.csv"):
    global RESOURCE_DATA
    RESOURCE_DATA = {}
    try:
        with open("resources_data.csv", "r") as f:
            lines = f.readlines()
            for line in lines[1:]:  # skip header
                data = line.strip().split(",")
                if len(data) >= 5:
                    name = data[0]
                    abundance = float(data[1])
                    r, g, b = int(data[2]), int(data[3]), int(data[4])
                    RESOURCE_DATA[name] = Resource(name,(r,g,b),abundance)
    except Exception as e:
        logger.error(f"Error loading resource data: {e}")

if __name__ == "__main__":
    load_resource_data("resources_data.csv")

    print(RESOURCE_DATA)