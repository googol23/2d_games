from world_object import WorldObject

import json
import pickle as pk
from pathlib import Path
from pydantic import BaseModel, ConfigDict

TREE_DATA = {}
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

def load_trees(filepath: str | None = None):
    """
    Load trees from Pickle binary if it exists, otherwise from JSON.
    Returns a list of Tree instances.
    If 'filepath' is provided, JSON is always loaded (ignoring binary).
    """
    project_root = Path(__file__).resolve().parent.parent
    trees_json_file = project_root / "json_files" / "trees.json"
    trees_pkl_file = project_root / "pkl_files" / "trees.pkl"

    trees = []

    # Only try binary if no JSON filepath is provided
    if filepath is None and Path(trees_pkl_file).exists():
        try:
            with open(trees_pkl_file, "rb") as f:
                trees = pk.load(f)
            print(f"Loaded {len(trees)} trees from binary.")
            return trees
        except Exception as e:
            print(f"Failed to load binary: {e}")

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

        tree_instance = Tree(model)
        trees.append(tree_instance)

    # Save binary for next time
    trees_pkl_file.parent.mkdir(exist_ok=True)
    with open(trees_pkl_file, "wb") as f:
        pk.dump(trees, f, protocol=pk.HIGHEST_PROTOCOL)

    print(f"Loaded {len(trees)} trees from JSON and saved binary.")
    return trees
