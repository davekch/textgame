from dataclasses import dataclass
from .base import CanDie, Movable, CanFight, Takable
from .behaviour import Behaves


@dataclass
class Creature(CanDie, Behaves, Movable):
    def die(self):
        super().die()
        for behaviour in self.behaviours.values():
            behaviour.switch_off()


@dataclass
class Monster(CanFight, Creature):
    pass


@dataclass
class TakableMonster(Takable, Monster):
    takable = False

    def die(self):
        self.takable = True
        return super().die()
