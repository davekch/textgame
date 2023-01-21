"""
textgame.things.base
=====================

This submodule defines the base classes :class:`Thing` and :class:`Movable` as well as
some dataclass mixins with reusable properties and methods.
"""

from dataclasses import dataclass
from random import Random
from ..messages import m


@dataclass
class Thing:
    """represents something that can be described"""

    id: str
    description: str

    def describe(self) -> m:
        return m(self.description)


@dataclass
class Movable(Thing):
    """represents a :class:`Thing` that has a name and location"""

    name: str
    initlocation: str


@dataclass
class Takable:
    """dataclass mixin for something that can be taken by the player"""

    takable: bool = True


@dataclass
class HasStrength:
    """dataclass mixin for something that has (variable) strength"""

    strength: float = 0
    strength_variation: float = 0

    def calculate_damage(self, random_engine: Random) -> float:
        # the state's random engine gets passed so that everything
        # is determined by the state's seed
        variation = random_engine.uniform(-1, 1) * self.strength_variation
        return abs(self.strength * (1 - variation))


@dataclass
class CanDie:
    """dataclass mixin for something that can die"""

    dead_description: str = ""
    health: float = 100

    @property
    def alive(self):
        return self.health > 0

    def die(self):
        self.health = -1
        self.description = self.dead_description or self.description
