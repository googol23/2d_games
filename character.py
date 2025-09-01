import knowledge_tree
import resources

import random
import numpy as np
from abc import ABC, abstractmethod
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

ENERGY_PER_TILE = 1
# Base class
class Character(ABC):
    def __init__(self, name, age=0, health=100, speed=10, energy=100):
        self.name = name
        self.age = age
        self.health = health
        self.speed = speed
        self.idle = True
        self.energy = energy
        self.current_speed = 0

        self.knowledge = knowledge_tree.KnowledgeTree()

    def age_up(self, years=1):
        self.age += years
        logger.debug(f"{self.name} is now {self.age} years old.")

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        logger.debug(f"{self.name} takes {amount} damage. Health = {self.health}")
        if self.health <= 0:
            logger.debug(f"{self.name} has died.")

    def __str__(self):
        return f"Name: {self.name}, Age: {self.age}, Health: {self.health}, Speed: {self.speed}"

# Movement-focused classes
class Walker(Character):
    def __init__(self, name, age=0, health=100, speed=10):
        super().__init__(name, age, health, speed)
        self.terrain_factor = {
            'water' : 0.2,
            'land' : 1,
            'air' : 0
        }

    def move(self):
        logger.debug(f"{self.name} walks on land.")


class Swimmer(Character):
    def __init__(self, name, age=0, health=100, speed=10):
        super().__init__(name, age, health, speed)
        self.terrain_factor = {
            'water' : 1,
            'land' : 0.01,
            'air' : 0
        }
    def move(self):
        logger.debug(f"{self.name} swims in water.")


class Flyer(Character):
    def __init__(self, name, age=0, health=100, speed=10):
        super().__init__(name, age, health, speed)
        self.terrain_factor = {
            'water' : 0.01,
            'land' : 0.2,
            'air' : 1
        }
    def move(self):
        logger.debug(f"{self.name} flies in the sky.")

# Human inherits from both Walker and Swimmer
class Human(Walker, Swimmer):
    def __init__(self, name, age=0, health=100, speed=10, skills=None):
        super().__init__(name, age, health, speed)
        self.tasks = []  # list of tasks
        self.inventory = defaultdict(float)

        # Default survival skills if none provided
        default_skills = {
            "Gathering": 0,
            "Foraging": 0,
            "Hunting": 0,
            "Fishing": 0,
            "Cooking": 0,
            "FirstAid": 0,
            "ShelterBuilding": 0,
            "Firecraft": 0,
            "Navigation": 0,
            "Tracking": 0,
            "Strength": 1,
            "Intelligence": 1,
            "Endurance": 1,
        }
        self.skills = skills or default_skills

    def collect_item(self, item, quantity=1) -> int:
        if quantity > 1:
            self.knowledge.try_unlocks(f"collected_{item.lower()}")

        item_carry_capacity = (self.max_carry_weight() - self.loaded_weight()) // self.knowledge.tree[item]['weight']
        if item_carry_capacity > self.knowledge.tree[item]['weight']:
            self.inventory[item] += item_carry_capacity

        return item_carry_capacity


    def max_carry_weight(self) -> float:
        return 10 + 2*self.skills['Strength']

    def loaded_weight(self) -> float:
        return np.sum([self.knowledge.tree[item]['weight'] for item in self.inventory])


    def add_task(self, task):
        self.tasks.append(task)

    def move(self):
        # You can specialize Human's behavior here
        logger.debug(f"{self.name} can both walk and swim, choosing the best option.")


# Example usage
if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    h = Human("Cody", age=25)
    print(h)

    for i in range(10):
        random_item = random.choice([item for item in h.knowledge.tree.keys()])
        item_quantity = random.randint(3,4)

        colledted = h.collect_item(random_item, item_quantity)
        logger.info(f"Collected {colledted} {random_item}")



