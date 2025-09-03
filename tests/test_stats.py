import unittest
from pathlib import Path
from stats import SkillSet, Skill

class TestSkillSet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        project_root = Path(__file__).resolve().parent.parent
        cls.skill_json = project_root / "json_files" / "stats_data.json"

    def setUp(self):
        self.skill_set = SkillSet.LoadSkillSet("Human", filepath=self.skill_json)

    def test_skills_loaded(self):
        # Ensure skills for the class are loaded
        self.assertTrue(len(self.skill_set) > 0)
        for skill_name, skill in self.skill_set.items():
            self.assertIsInstance(skill, Skill)

    def test_try_to_learn(self):
        # Pick a skill and trigger
        skill_name = next(iter(self.skill_set._skills))
        skill = self.skill_set[skill_name]
        initial_points = skill.points

        # Use one of its triggers (if any)
        if skill.triggers:
            trigger_event = next(iter(skill.triggers))
            self.skill_set.try_to_learn(trigger_event)
            self.assertGreater(skill.points, initial_points)

    def test_add_skill(self):
        self.skill_set.AddSkill("Alchemy")
        self.assertIn("Alchemy", self.skill_set)
        self.assertIsInstance(self.skill_set["Alchemy"], Skill)

if __name__ == "__main__":
    unittest.main()
