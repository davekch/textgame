"""
textgame.things.items
========================

This submodule defines classes for any passive thing that might be present in a room and
can be picked up by the player.
"""

from dataclasses import dataclass
from .base import Takable, Movable, HasStrength
from .storage import Contains


@dataclass
class Item(Takable, Movable):
    """represents something that has value. Is takable and movable"""

    value: int = 0


class Lightsource(Item):
    """represents an item that produces light"""


@dataclass
class Key(Item):
    key_id: int = 0


@dataclass
class Weapon(HasStrength, Item):
    pass


@dataclass
class Container(Contains, Item):
    """represents an item that can contain other items"""
