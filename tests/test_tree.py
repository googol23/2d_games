import unittest
from pathlib import Path
import pickle
import json

from world.tree import Tree, TreeModel

class TestTree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).resolve().parent.parent
        cls.json_file = cls.project_root / "json_files" / "trees.json"
        cls.pkl_file = cls.project_root / "pkl_files" / "trees.pkl"

    def test_load_trees_from_json_or_pickle(self):
        # Load trees (will use pickle if exists, else JSON)
        trees = Tree.load_trees()
        self.assertIsInstance(trees, list)
        self.assertGreater(len(trees), 0)
        for tree in trees:
            self.assertIsInstance(tree, Tree)
            self.assertIsInstance(tree.name, str)
            self.assertIsInstance(tree.growth_rate, int)
            self.assertIsInstance(tree.log_yield, int)
            self.assertIsInstance(tree.temp_range, list)

    def test_repr(self):
        # Pick one tree from JSON
        with open(self.json_file, "r") as f:
            raw_data = json.load(f)
        name, data = next(iter(raw_data.items()))
        data["name"] = name
        if "yield" in data:
            data["log_yield"] = data.pop("yield")
        tree = Tree(TreeModel(**data))
        rep = repr(tree)
        self.assertIn(tree.name, rep)
        self.assertIn(tree.wood_type, rep)
        self.assertIn(str(tree.growth_rate), rep)

    def test_pickle_consistency(self):
        # Force save/load cycle to ensure pickle works
        trees_json = Tree.load_trees(filepath=self.json_file)
        with open(self.pkl_file, "wb") as f:
            pickle.dump(trees_json, f)

        with open(self.pkl_file, "rb") as f:
            trees_pickle = pickle.load(f)

        self.assertEqual(len(trees_json), len(trees_pickle))
        for t_json, t_pickle in zip(trees_json, trees_pickle):
            self.assertEqual(t_json.name, t_pickle.name)
            self.assertEqual(t_json.growth_rate, t_pickle.growth_rate)
            self.assertEqual(t_json.log_yield, t_pickle.log_yield)

if __name__ == "__main__":
    unittest.main()
