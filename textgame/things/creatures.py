"""
textgame.things.creatures
==========================

This module contains classes for Things that can die and behave.
"""
from dataclasses import dataclass
from .base import CanDie, Movable, HasStrength, Takable
from .behaviour import Behaves


@dataclass
class Creature(CanDie, Behaves, Movable):
    """represents a creature. When the creature dies, all behaviours are switched off"""

    def die(self):
        super().die()
        for behaviour in self.behaviours.values():
            behaviour.switch_off()


@dataclass
class Monster(HasStrength, Creature):
    """represents a creature that can fight"""


@dataclass
class TakableMonster(Takable, Monster):
    """represents a monster that can be picked up by the player when dead"""

    takable = False

    def die(self):
        self.takable = True
        return super().die()
