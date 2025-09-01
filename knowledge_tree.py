import json
import random
from graphviz import Digraph
from pydantic import BaseModel, RootModel
from typing_extensions import Self
from typing import List, Dict, Union, Optional

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
    prereqs: List[str]
    rules: List[Union[EventRule, ChanceRule]]
    weight: float
    description: Optional[str]
    crafting: Optional[Dict[str,int]] = None

class KnowledgeTree(RootModel[Dict[str, Item]]):

    @classmethod
    def LoadTree(cls, filepath="knowledge.json") -> Self:
        """
        Load knowledge nodes from JSON file.
        Preserves all fields from JSON (e.g., description, crafting, weight),
        but replaces raw rules with callable functions.
        """
        with open(filepath, "r") as f:
            return cls.model_validate_json(f.read())

        for item in self.root.values():
            item.rules = [ChanceRule(**r) if "chance" in r else EventRule(**r) for r in item.rules]

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

    def known(self):
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


if __name__ == "__main__":
    import time

    # Initialize knowledge tree from JSON
    tree = KnowledgeTree.LoadTree("knowledge.json")

    # Initial visualization
    tree.visualize("my_knowledge_tree")

    # Simulate random events until all knowledge is unlocked
    while not tree.all_unlocked():
        events = []
        for item in tree.known():
            if tree.__getitem__(item).crafting is None:
                events.append(f"collected_{item.lower()}")
            else:
                events.append(f"crafted_{'_'.join(item.lower().split())}")


        event = random.choice(events)
        tree.try_unlocks(event)
        tree.visualize("my_knowledge_tree")
        # time.sleep(0.5)
    
