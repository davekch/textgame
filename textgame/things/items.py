from dataclasses import dataclass
from .base import Takable, Movable, HasStrength
from .storage import Contains


@dataclass
class Item(Takable, Movable):
    value: int = 0


class Lightsource(Item):
    pass


@dataclass
class Key(Item):
    key_id: int = 0


@dataclass
class Weapon(HasStrength, Item):
    pass


@dataclass
class Container(Contains, Item):
    pass
