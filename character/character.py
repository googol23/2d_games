import knowledge_tree
import resources
import stats.stats as stats
from agent import Agent

import sys


import random
import numpy as np
from abc import ABC, abstractmethod
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Base class
class Character(Agent, ABC):
    def __init__(self, name:str, age:int=0, health:int=100, speed:float=1, energy:float=100):
        super().__init__(speed=speed)
        self.name = name
        self.age = age
        self.health = health
        self.idle = True
        self.energy = energy
        self.current_speed = 0

        self.knowledge = knowledge_tree.KnowledgeTree.LoadTree()
        self.skills_set = stats.SkillSet.LoadSkillSet(class_name=type(self).__name__)

    def age_up(self, years=1):
        self.age += years
        logger.debug(f"{self.name} is now {self.age} years old.")

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        logger.debug(f"{self.name} takes {amount} damage. Health = {self.health}")
        if self.health <= 0:
            logger.debug(f"{self.name} has died.")

    def __str__(self):
        return f"Name: {self.name}, Age: {self.age}, Health: {self.health}, Speed: {self.get_speed()}"



class Human(Character):
    def __init__(self, name:str, age:int, health:float, speed:float):
        super().__init__(name, age, health, speed)
        self.tasks = []  # list of tasks
        self.inventory = defaultdict(float)
        self.terrain_factor = {
            'water' : 0.02,
            'land' : 1.0,
            'air' : 0
        }

    def collect_item(self, item, quantity=1) -> int:
        if quantity > 1:
            self.handle_event(f"collected_{item.lower()}")

        item_carry_capacity = (self.max_carry_weight() - self.loaded_weight()) // self.knowledge.__getitem__(item).weight
        if item_carry_capacity > self.knowledge.__getitem__(item).weight:
            self.inventory[item] += item_carry_capacity

        return item_carry_capacity

    def handle_event(self, event: str) -> None:
        """
        Dispatch an event to unlock items and improve player skills.
        Uses each skill's triggers dynamically.
        """
        # Step 1: normal unlock handling
        self.knowledge.try_unlocks(event)

        # Step 2: skill progression from triggers
        self.skills_set.try_to_learn(event)


    def max_carry_weight(self) -> float:
        return 10 + 2*self.skills_set['Strength'].level

    def loaded_weight(self) -> float:
        return np.sum([self.knowledge.__getitem__(item).weight for item in self.inventory])


    def add_task(self, task):
        self.tasks.append(task)

    def move(self):
        # You can specialize Human's behavior here
        logger.debug(f"{self.name} can both walk and swim, choosing the best option.")


# Example usage
if __name__ == "__main__":
    import time
    from pympler import asizeof
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    h = Human("Cody", age=25)

    # Simulate random events until all knowledge is unlocked

    size_bytes = asizeof.asizeof(h)
    size_mb = size_bytes / (1024 ** 2)

    print(f"Human instance size: {size_mb:.6f} MB")

    while not h.knowledge.all_unlocked():
        events = []
        for item in h.knowledge.known():
            if h.knowledge[item].crafting is None:
                events.append(f"gathering_{item.lower()}")
            else:
                events.append(f"crafting_{'_'.join(item.lower().split())}")

        # Pick a random event
        event = random.choice(events)
        # print(event)

        # Handle event: unlock items and increment skills
        h.handle_event(event)

        # Optional: visualize knowledge tree
        h.knowledge.visualize("my_knowledge_tree")

        stats.draw_skills_bitmap(h)

        time.sleep(0.1)