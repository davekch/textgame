"""
textgame.things
=================

This module defines classes for all *things* that are present in the game such as
Items, Creatures and also behaviours for these things.

.. toctree::

    textgame.things.base
    textgame.things.items
    textgame.things.behaviour
    textgame.things.creatures
"""

from .base import (
    Thing,
    Movable,
    Takable,
    HasStrength,
    CanDie,
    CanFight,
)
from .items import Item, Lightsource, Key, Weapon, Container
from .creatures import Creature, Monster, TakableMonster
from .behaviour import Behaviour, BehaviourSequence, behaviour_factory, Behaves
from .storage import StorageManager, Store, Contains
