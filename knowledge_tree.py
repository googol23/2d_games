import json
import random
from graphviz import Digraph

class KnowledgeTree:
    def __init__(self, filepath="knowledge.json"):
        self.tree = {}
        self.load_tree(filepath)

    def load_tree(self, filepath):
        """Load knowledge nodes from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)

        # Initialize tree with rules converted to functions
        for node_name, node_data in data.items():
            self.tree[node_name] = {
                "unlocked": node_data.get("unlocked", False),
                "prereqs": node_data.get("prereqs", []),
                "rules": [self._make_rule(r) for r in node_data.get("rules", [])]
            }

    def _make_rule(self, rule_dict):
        """Convert JSON rule definition to a function"""
        if rule_dict["type"] == "chance_on_event":
            event_name = rule_dict["event"]
            chance = rule_dict["chance"]
            # This function receives the event name that just happened
            return lambda event: event == event_name and random.random() < chance
        raise ValueError(f"Unknown rule type: {rule_dict['type']}")

    def try_unlocks(self, events):
        """Check all locked nodes against rules + prereqs"""
        for node, data in self.tree.items():
            if not data["unlocked"]:
                if all(self.tree[p]["unlocked"] for p in data["prereqs"]):
                    if all(rule(events) for rule in data["rules"]):
                        data["unlocked"] = True
                        print(f"Unlocked knowledge: {node}")

    def knows(self, item):
        return self.tree.get(item, {}).get("unlocked", False)

    def known(self, item):
        return [name for name, data in self.tree.items() if data["unlocked"]]

    def all_unlocked(self):
        """Return True if every knowledge node is unlocked"""
        return all(data["unlocked"] for data in self.tree.values())

    def visualize(self, filename="knowledge_tree", view=False):
        dot = Digraph(comment="Knowledge Tree")

        # Add nodes
        for name, data in self.tree.items():
            color = "green" if data["unlocked"] else "red"
            dot.node(name, name, color=color, style="filled", fillcolor=color)

        # Add edges (prerequisites)
        for name, data in self.tree.items():
            for prereq in data["prereqs"]:
                dot.edge(prereq, name)

        dot.render(filename, view=view, format="png")
