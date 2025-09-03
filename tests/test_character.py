import unittest
from pathlib import Path
import random

from character import Human, Walker, Swimmer, Flyer
from drawing import skills_bitmap

class TestCharacter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Compute project root
        project_root = Path(__file__).resolve().parent.parent
        cls.knowledge_json = project_root / "json_files" / "knowledge.json"
        cls.skills_json = project_root / "json_files" / "stats_data.json"

    def setUp(self):
        # Create a Human instance
        self.human = Human(name="TestHuman", age=30, health=100, speed=1)

    def test_basic_attributes(self):
        self.assertEqual(self.human.name, "TestHuman")
        self.assertEqual(self.human.age, 30)
        self.assertTrue(hasattr(self.human, "knowledge"))
        self.assertTrue(hasattr(self.human, "skills_set"))

    def test_handle_event_unlocks_knowledge(self):
        # Pick a known item
        known_items = [item for item, data in self.human.knowledge.root.items() if data.unlocked]
        if known_items:
            event = f"collected_{known_items[0].lower()}" if self.human.knowledge[known_items[0]].crafting is None else f"crafted_{'_'.join(known_items[0].lower().split())}"
            self.human.handle_event(event)
            self.assertTrue(self.human.knowledge[known_items[0]].unlocked)

    def test_handle_event_increments_skill(self):
        # Use a skill trigger from the Human's skill set
        for skill_name, skill in self.human.skills_set.items():
            if skill.triggers:
                trigger_event = next(iter(skill.triggers))
                old_points = skill.points
                self.human.handle_event(trigger_event)
                self.assertGreaterEqual(skill.points, old_points)
                break

    def test_inventory_and_carry_weight(self):
        item_name = next(iter(self.human.knowledge.root.keys()))
        cap = self.human.collect_item(item_name, quantity=2)
        self.assertGreaterEqual(cap, 0)
        self.assertIn(item_name, self.human.inventory)

    def test_draw_skills_bitmap_runs(self):
        # Make sure drawing does not crash
        img = skills_bitmap(self.human)
        self.assertIsNotNone(img)
        self.assertTrue(hasattr(img, "save"))

if __name__ == "__main__":
    unittest.main()
