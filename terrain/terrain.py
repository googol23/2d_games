import json
import logging
from pathlib import Path
from pydantic import BaseModel, ValidationError, ConfigDict

logger = logging.getLogger(__name__)

TERRAIN_DATA = {}  # name → Terrain object or dict


# Minimal validation model
class Terrain(BaseModel):
    name: str
    color: tuple[int, int, int] = (0, 0, 0)
    texture: str | None = None
    resources: tuple[str, ...] = ()
    vegetation: tuple[str, ...] = ()

    model_config = ConfigDict(extra="forbid", frozen=True)

    # allow color to come as a list
    @classmethod
    def parse_color(cls, color):
        if isinstance(color, list):
            return tuple(color)
        return color

    @classmethod
    def from_dict(cls, data: dict):
        data = data.copy()
        if "color" in data:
            data["color"] = cls.parse_color(data["color"])
        data["resources"] = tuple(data.get("resources", []))
        data["vegetation"] = tuple(data.get("vegetation", []))
        return cls(**data)

    def __str__(self):
        return f"{self.name}: Color={self.color}, Resources={self.resources}, Vegetation={self.vegetation}"

    def __repr__(self):
        return self.__str__()


def load_terrains_data(json_file_path: str | None = None):

    """
    Loads terrain data with validation, storing into TERRAIN_DATA for fast access.
    """
    try:
        if json_file_path is None:
            project_root = Path(__file__).resolve().parent.parent
            json_file_path = project_root / "json_files" / "terrains_data.json"
        with open(json_file_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading terrain data from {json_file_path}: {e}")
        return

    TERRAIN_DATA.clear()
    for terrain_info in data:
        try:
            terrain = Terrain.from_dict(terrain_info)
            TERRAIN_DATA[terrain.name] = terrain
        except ValidationError as e:
            logger.error(f"Validation failed for terrain: {terrain_info}. Error: {e}")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)  # <-- set logger level

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    load_terrains_data()
    print(TERRAIN_DATA)
