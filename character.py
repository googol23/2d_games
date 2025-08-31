from abc import ABC, abstractmethod
import logging
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
    def move(self):
        logger.debug(f"{self.name} walks on land.")


class Swimmer(Character):
    def move(self):
        logger.debug(f"{self.name} swims in water.")


class Flyer(Character):
    def move(self):
        logger.debug(f"{self.name} flies in the sky.")

# Human inherits from both Walker and Swimmer
class Human(Walker, Swimmer):
    def __init__(self, name, age=0, health=100, speed=10, skills=None):
        super().__init__(name, age, health, speed)
        self.tasks = []  # list of tasks
        self.carrying = None  # what the character carries
        self.inventory = {}

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
    h.move()            # uses Human's custom move()
    h.age_up(5)         # aging
    h.take_damage(30)   # damage system
    h.add_task({
        "action" : "G",
        "item"   : "S",
        "target" : "H"
    })
    print(h)
