from dataclasses import dataclass
from .base import _CanDie, Movable, _CanFight, Takable
from .behaviour import _Behaves


@dataclass
class Creature(_CanDie, _Behaves, Movable):
    def die(self):
        super().die()
        for behaviour in self.behaviours.values():
            behaviour.switch_off()


@dataclass
class Monster(_CanFight, Creature):
    pass


@dataclass
class TakableMonster(Takable, Monster):
    takable = False

    def die(self):
        self.takable = True
        return super().die()
