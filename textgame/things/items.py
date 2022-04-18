from dataclasses import dataclass
from .base import Takable, Movable, _HasStrength
from .storage import _Contains


@dataclass
class Item(Takable, Movable):
    value: int = 0


class Lightsource(Item):
    pass


@dataclass
class Key(Item):
    key_id: int = 0


@dataclass
class Weapon(_HasStrength, Item):
    pass


@dataclass
class Container(_Contains, Item):
    pass
