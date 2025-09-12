import knowledge_tree
from stats import SkillSet
from agent import Agent

from abc import ABC

import logging
logger = logging.getLogger(__name__)

# Base class
class Character(Agent, ABC):
    def __init__(self, name:str, age:int=0, max_health:int=100, base_speed:float=1, max_energy:int=100):
        super().__init__(base_speed=base_speed)
        self.name = name
        self.age = age
        self.max_health = max_health
        self.max_energy = max_energy

        self.current_hp:float = 1. # percent of max_health
        self.current_ep:float = 1. # percent of max_health

        self.knowledge = knowledge_tree.KnowledgeTree.LoadTree()
        self.skills_set = SkillSet.LoadSkillSet(class_name=type(self).__name__)

    @property
    def speed(self) -> float:
        return super().speed * self.current_hp * self.current_ep

    def age_up(self, years=1):
        self.age += years
        logger.debug(f"{self.name} is now {self.age} years old.")

    def take_damage(self, amount):
        self.max_health = max(0, self.max_health - amount)
        logger.debug(f"{self.name} takes {amount} damage. Health = {self.max_health}")
        if self.max_health <= 0:
            logger.debug(f"{self.name} has died.")

    def __str__(self):
        return f"Name: {self.name}, Age: {self.age}, Health: {self.max_health}, Speed: {self.speed}"

