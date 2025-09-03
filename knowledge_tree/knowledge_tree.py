import json
import random
from pathlib import Path
from pydantic import BaseModel, RootModel
from graphviz import Digraph

from typing_extensions import Self

class EventRule(BaseModel):
    event: str

    def __call__(self, event: str) -> bool:
        return event == self.event

class ChanceRule(EventRule):
    chance: float

    def __call__(self, event: str) -> bool:
        return super().__call__(event) and (random.random() < self.chance)

class Item(BaseModel):
    unlocked: bool
    prereqs: list[str]
    rules: list[ChanceRule | EventRule] = []
    weight: float
    description: str | None = None
    crafting: dict[str,int] | None = None

class Food(Item):
    nutrition: int  # how much it restores (could be negative for poison)

class Tool(Item):
    durability: int
    damage: int

class KnowledgeTree(RootModel[dict[str, Item]]):

    @classmethod
    def LoadTree(cls, filepath: str | None = None) -> Self:
        """
        Load knowledge nodes from JSON file.
        Preserves all fields from JSON (e.g., description, crafting, weight),
        but replaces raw rules with callable functions.
        """
        if filepath is None:
            PROJECT_ROOT = Path(__file__).resolve().parent.parent
            filepath = PROJECT_ROOT / "json_files" / "knowledge.json"

        with open(filepath, "r") as f:
            instance =  cls.model_validate_json(f.read())

        for item in instance.root.values():
            item.rules = [
                ChanceRule(**r) if isinstance(r, dict) and "chance" in r else
                EventRule(**r) if isinstance(r, dict) else
                r  # already a rule instance
                for r in item.rules
            ]

        return instance

    def __getitem__(self, item:str) -> Item:
        return self.root[item]

    def try_unlocks(self, event: str) -> None:
        """
        Try to unlock all currently locked nodes given the latest event.
        Unlock occurs if:
          1. All prerequisites are unlocked.
          2. All rules evaluate to True with the given event.
        """
        for node, data in self.root.items():
            if not data.unlocked:
                # 1. Check prerequisites
                if all(self.root[p].unlocked for p in data.prereqs):
                    # 2. Check all rules against this event
                    if all(rule(event) for rule in data.rules):
                        data.unlocked = True
                        # Print description if available, otherwise fallback
                        msg = data.description or f"{node} unlocked!"
                        print(msg)

    def knows(self, item:str) -> bool:
        """Return True if the given item is unlocked in the tree"""
        return self.root[item].unlocked if item in self.root else False

    def known(self) -> list[str]:
        """Return a list of all unlocked items"""
        return [name for name, data in self.root.items() if data.unlocked]

    def all_unlocked(self):
        """Return True if every node in the tree is unlocked"""
        return all(data.unlocked for data in self.root.values())

    def visualize(self, filename="knowledge_tree", view=False):
        """
        Render the knowledge tree as a PNG image using Graphviz.
        Green = unlocked, Red = locked
        """
        dot = Digraph(comment="Knowledge Tree")

        # Add nodes
        for name, data in self.root.items():
            color = "green" if data.unlocked else "red"
            dot.node(name, name, color=color, style="filled", fillcolor=color)

        # Add edges (dependencies)
        for name, data in self.root.items():
            for prereq in data.prereqs:
                dot.edge(prereq, name)

        dot.render(filename, view=view, format="png")
