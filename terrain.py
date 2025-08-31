import json

import logging

logger = logging.getLogger(__name__)

TERRAIN_DATA = {}

class Terrain:
    def __init__(self, name, color=None, texture=None, resources=None, vegetation=None):
        self.name = name
        self.color = color
        self.texture = texture
        self.resources = resources or []
        self.vegetation = vegetation or []

    def __str__(self):
        return f"{self.name}: Color={self.color}, Resources={self.resources}, Vegetation={self.vegetation}"

    def __repr__(self):
        return self.__str__()

def load_terrains_data(json_file_path):
    """
    Loads terrain data from a JSON file and fills TERRAIN_DATA.
    The JSON should be a list of objects with keys: name, resources, vegetation, color.
    """
    try:
        with open(json_file_path, "r") as f:
            data = json.load(f)
        logger.debug(f"Loading terrain data from: {data}")
    except Exception as e:
        logger.error(f"Error loading terrain data from {json_file_path}: {e}")
        return

    for terrain_info in data:
        logger.debug(f"Loading terrain: {terrain_info}")
        name = terrain_info.get("name")
        resources = terrain_info.get("resources", [])
        vegetation = terrain_info.get("vegetation", "")
        color = tuple(terrain_info.get("color", (0, 0, 0)))
        TERRAIN_DATA[name] = Terrain(
            name=name,
            color=color,
            resources=resources,
            vegetation=vegetation
        )

if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)  # <-- set logger level

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    load_terrains_data("terrains_data.json")
    print(len(TERRAIN_DATA))
