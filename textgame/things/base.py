from dataclasses import dataclass
from random import Random
from ..messages import m


@dataclass
class Thing:
    id: str
    description: str

    def describe(self) -> m:
        return m(self.description)


@dataclass
class Movable(Thing):
    name: str
    initlocation: str


@dataclass
class Takable:
    takable: bool = True


@dataclass
class HasStrength:
    strength: float = 0
    strength_variation: float = 0

    def calculate_damage(self, random_engine: Random) -> float:
        # the state's random engine gets passed so that everything
        # is determined by the state's seed
        variation = random_engine.uniform(-1, 1) * self.strength_variation
        return abs(self.strength * (1 - variation))


@dataclass
class CanDie:
    dead_description: str = ""
    alive: bool = True

    def die(self):
        self.alive = False
        self.description = self.dead_description or self.description


@dataclass
class CanFight(HasStrength):
    health: float = 100
    fight_message: str = ""
    win_message: str = ""  # when the player wins
    loose_message: str = ""  # when the player looses
