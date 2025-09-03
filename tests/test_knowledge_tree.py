import unittest
from unittest.mock import patch
from knowledge_tree import KnowledgeTree
import random

class TestKnowledgeTreeWithJSON(unittest.TestCase):

    def setUp(self):
        # Load the actual knowledge tree from your JSON
        self.tree = KnowledgeTree.LoadTree()

    def test_initial_state(self):
        # At the beginning, some items may be locked
        unlocked_items = self.tree.known()
        all_items = list(self.tree.root.keys())
        self.assertTrue(len(unlocked_items) <= len(all_items))
        # Make sure all unlocked items exist in the tree
        for item in unlocked_items:
            self.assertIn(item, self.tree.root)

    def test_try_unlocks_with_event(self):
        # Pick an event from the tree to unlock an item
        # Find an item with no prereqs for simplicity
        for name, item in self.tree.root.items():
            if not item.prereqs and not item.unlocked:
                event_name = f"gathering_{name.lower()}" if item.crafting is None else f"crafted_{'_'.join(name.lower().split())}"
                # Patch random to force ChanceRules to succeed
                with patch("random.random", return_value=0):
                    self.tree.try_unlocks(event_name)
                self.assertTrue(self.tree.knows(name))
                break

    def test_all_unlocked_method(self):
        # This just ensures the method runs without error
        result = self.tree.all_unlocked()
        self.assertIsInstance(result, bool)

    def test_unlock_entire_tree(self):
        with patch("random.random", return_value=0):
            while not self.tree.all_unlocked():
                events = []
                for item in self.tree.known():
                    node = self.tree[item]
                    if node.crafting is None:
                        events.append(f"gathering_{item.lower()}")
                    else:
                        events.append(f"crafting_{'_'.join(item.lower().split())}")

                if not events:
                    break  # safety fallback

                for event in events:
                    self.tree.try_unlocks(event)


if __name__ == "__main__":
    unittest.main()
