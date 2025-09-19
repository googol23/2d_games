from world_object import WorldObject

import json
import pickle as pk
from pathlib import Path
from pydantic import BaseModel, ConfigDict

import logging
logger = logging.getLogger("tree")

class TreeModel(BaseModel):
    name: str
    growth_rate: int          # years to harvest
    water_consumption: float
    temp_range: list[int]     # [min_temp, max_temp]
    log_yield: int               # logs per tree
    seed_yield: int           # seeds per year
    wood_type: str
    description: str = ""
    unlocked: bool = True
    texture: str | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)

class Tree(WorldObject):

    def __init__(self, model: TreeModel):
        self.name = model.name
        self.growth_rate = model.growth_rate
        self.water_consumption = model.water_consumption
        self.temp_range = model.temp_range
        self.log_yield = model.log_yield
        self.seed_yield = model.seed_yield
        self.wood_type = model.wood_type
        self.description = model.description
        self.unlocked = model.unlocked
        self.texture = model.texture

        self.age = self.growth_rate
        self.hp = (1+0.5*int(self.wood_type == "hardwood")) * self.age

    def __repr__(self):
        return f"<Tree {self.name}, {self.wood_type}, harvest in {self.growth_rate} years>"


TREE_DATA:dict[str,TreeModel] = {}
def load_trees(filepath: str | None = None) -> dict[str, TreeModel]:
    """
    Load trees from Pickle binary if it exists, otherwise from JSON.
    Populates TREE_DATA with TreeModel instances.
    If 'filepath' is provided, JSON is always loaded (ignoring binary).
    Returns TREE_DATA.
    """
    global TREE_DATA

    project_root = Path(__file__).resolve().parent.parent
    trees_json_file = project_root / "json_files" / "trees.json"
    trees_pkl_file = project_root / "pkl_files" / "trees.pkl"


    # Load from binary if exists and no JSON filepath is given
    if filepath is None and trees_pkl_file.exists():
        try:
            with open(trees_pkl_file, "rb") as f:
                TREE_DATA.clear()           # remove old entries
                TREE_DATA.update(pk.load(f))  # fill in from pickle
            logger.info(f"Loaded {len(TREE_DATA)} trees from binary.")
            return TREE_DATA
        except Exception as e:
            logger.warning(f"Failed to load binary: {e}")

    # Load from JSON
    filepath = filepath or trees_json_file
    with open(filepath, "r") as f:
        raw_data = json.load(f)

    for name, data in raw_data.items():
        data["name"] = name
        if "yield" in data:
            data["log_yield"] = data.pop("yield")

        model = TreeModel(**data)
        TREE_DATA[name] = model
        logger.info(f"Added TreeModel for {name}")

    # Save binary for next time
    trees_pkl_file.parent.mkdir(exist_ok=True)
    with open(trees_pkl_file, "wb") as f:
        pk.dump(TREE_DATA, f, protocol=pk.HIGHEST_PROTOCOL)

    logger.info(f"Loaded {len(TREE_DATA)} trees from JSON and saved binary.")
    return TREE_DATA

