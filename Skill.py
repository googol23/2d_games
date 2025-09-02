import numpy as np
from collections import defaultdict
import json
from typing import Optional, List, Union, Dict
from pydantic import BaseModel, Field
import math

from graphviz import Digraph

# Single skill data
class SkillData(BaseModel):
    name: str
    triggers: Dict[str,float]

# Root model for the full JSON
class ClassesData(BaseModel):
    skills: Dict[str, SkillData]  # master skill definitions
    classes: Dict[str, List[str]] # class name -> list of skill names
# --------------------------

class Skill:
    def __init__(self, name: str, level: int = 0, triggers: Dict[str,float] = {}):
        self.name = name
        self.level = level
        self.points = 0
        self.points_to_next_level = 0
        self.triggers = {trigger.lower(): weight for trigger, weight in triggers.items()}

        # Precompute thresholds once
        self.max_level = 100
        self.base = 10      # points for level 1
        self.growth = 2.2   # exponential growth rate
        self.level = 0
        self.level_thresholds = [int(self.base * (self.growth ** i)) for i in range(self.max_level)]


    def increment(self, amount: int = 1):
        self.points += amount

        # Increase level based on precomputed thresholds
        while self.level + 1 < len(self.level_thresholds) and self.points >= self.level_thresholds[self.level + 1]:
            self.level += 1

        # Points needed for next level
        if self.level + 1 < len(self.level_thresholds):
            self.points_to_next_level = self.level_thresholds[self.level + 1]
        else:
            self.points_to_next_level = self.level_thresholds[-1]


    def __str__(self):
        return f"{self.name}: {self.level:>4} ({self.points:>4})"


class SkillSet:
    """
    Container for Skill objects. Can load skills from a JSON file based on a class name.
    """
    skill_data_file = "skills_data.json"  # JSON file path

    def __init__(self):
        self._skills: defaultdict[str, Skill] = {}

    def AddSkill(self, skill:Union[Skill, str]) -> None:
        """
        Add a Skill object or a string (which will create a Skill) to the set.
        """
        if isinstance(skill, str):
            skill = Skill(skill)  # create a Skill
        self._skills[skill.name] = skill

    def try_to_learn(self, event: str):
        """
        Increment all skills whose triggers are contained within the event.
        Automatically applies Intelligence bonus if the skill exists.
        """
        intelligence_level = self._skills.get("Intelligence").level if "Intelligence" in self._skills else 0
        event_words = set(event.lower().split("_"))
        for skill in self._skills.values():
            for trigger, weight in skill.triggers.items():
                if trigger in event_words:
                    points_gained = int(weight + 0.5 * intelligence_level)
                    skill.increment(points_gained)

    def __getitem__(self, name: str) -> Skill:
        return self._skills[name]

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills

    def items(self):
        """Return an iterator over (skill_name, Skill) pairs."""
        return self._skills.items()

    def __str__(self):
        output = ""
        for name, skill in self._skills.items():
            output += f"{name:<15} : {skill.level:<5} ({skill.points}/{skill.points_to_next_level}) Learn by: " + ",".join(skill.triggers) + "\n"

        return output

    @classmethod
    def LoadSkillSet(cls, class_name: str, filepath: str = None) -> "SkillSet":
        """
        Load skills for a given class name from JSON using modern Pydantic validation.
        """
        filepath = filepath or cls.skill_data_file

        with open(filepath, "r") as f:
            raw_data = json.load(f)

        # Convert to ClassesData by injecting 'name' into each skill
        for skill_name, skill_dict in raw_data['skills'].items():
            skill_dict['name'] = skill_name

        validated_data = ClassesData.model_validate(raw_data)

        if class_name not in validated_data.classes:
            raise ValueError(f"No skill set defined for class '{class_name}'")

        skill_set = cls()
        for skill_name in validated_data.classes[class_name]:
            master_skill = validated_data.skills[skill_name]
            skill_set.AddSkill(Skill(
                name=master_skill.name,
                triggers=master_skill.triggers
            ))

        return skill_set

from PIL import Image, ImageDraw, ImageFont

def draw_skills_bitmap(player, width: int = 300, padding: int = 10, line_height: int = 25):
    """
    Returns a PIL Image (RGBA) representing the player's skills with transparency.
    Uses player.skill_set which contains Skill objects.
    """
    font = ImageFont.load_default()

    # Suppose you want to align colons after the longest skill name
    max_name_length = max(len(name) for name, skill in player.skills_set.items())

    # Prepare lines from the SkillSet
    lines = [f"{name:<{max_name_length}}: {skill.level:>4} ({skill.points:>4}/{skill.points_to_next_level})" for name, skill in player.skills_set.items()]

    # Compute dynamic width based on longest line
    width = int(max(font.getlength(line) for line in lines) + 2 * padding)

    # Compute height
    height = padding * 2 + line_height * (len(lines) + 1)

    # Create transparent image
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw title
    draw.text((padding, padding), f"=== {player.name} ===", font=font, fill=(255, 255, 255, 255))

    # Draw each skill
    y = padding + line_height
    for name, skill in player.skills_set.items():
        draw.text((padding, y), f"{name:<13}: {skill.level:>4} ({skill.points:>4}/{skill.points_to_next_level})", font=font, fill=(255, 255, 255, 255))
        y += line_height

    # Optionally save image
    img.save(f"{player.name}_skills.png")
    return img


if __name__ == "__main__":
    import character
    h = character.Human("Cody", age=25)
    draw_skills_bitmap(h)
    print(h.skills_set)

    dot = Digraph(comment='Skill Trigger Graph', format='png')

    # Add nodes
    for skill, skill_obj in h.skills_set.items():
        dot.node(skill)

    # Add edges with weights
    for skill, skill_obj in h.skills_set.items():
        for trigger, weight in skill_obj.triggers.items():
            dot.edge(trigger, skill, label=str(weight))

    # Render to file
    dot.render("skill_graph.png", cleanup=True)

