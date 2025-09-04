import json
import tempfile
from pathlib import Path

import pytest

from world.tree import Tree, TreeModel, load_trees


def test_tree_initialization_and_repr():
    model = TreeModel(
        name="Oak",
        growth_rate=10,
        water_consumption=5.0,
        temp_range=[0, 30],
        log_yield=20,
        seed_yield=5,
        wood_type="hardwood",
        description="Strong tree",
    )

    tree = Tree(model)

    # Check basic attributes
    assert tree.name == "Oak"
    assert tree.age == 10  # age set equal to growth_rate
    assert tree.hp == (1 + 0.5 * 1) * 10  # hardwood → hp multiplier
    assert "Oak" in repr(tree)
    assert "hardwood" in repr(tree)


def test_load_trees_from_json(tmp_path: Path):
    # Create fake JSON file with minimal tree data
    fake_json = tmp_path / "trees.json"
    data = {
        "Pine": {
            "growth_rate": 8,
            "water_consumption": 3.0,
            "temp_range": [-5, 25],
            "log_yield": 15,
            "seed_yield": 4,
            "wood_type": "softwood",
            "description": "Fast growing tree",
        }
    }
    fake_json.write_text(json.dumps(data))

    # Force load from our temp JSON
    trees = load_trees(filepath=fake_json)

    # We expect TREE_DATA to be filled and list of models returned
    assert isinstance(trees, list)
    assert "Pine" in trees or "Pine" in repr(trees)  # depends how you extend load_trees
