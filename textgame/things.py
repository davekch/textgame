from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from random import Random
from typing import List, Set, Dict, Any, Callable, Optional, Type
from functools import wraps
from collections import defaultdict
from .messages import m
from .registry import behaviour_registry
from .exceptions import (
    ConfigurationError,
    StoreLimitExceededError,
    UniqueConstraintError,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # State is only used as a type-hint in this file
    from .state import State

import logging

logger = logging.getLogger("textgame.things")
logger.addHandler(logging.NullHandler())


@dataclass
class Thing:
    id: str
    name: str
    description: str
    initlocation: str

    def describe(self) -> m:
        return m(self.description)


def _require_thing_exists(func: Callable) -> Callable:
    @wraps(func)
    def decorated_method(self: StorageManager, thing_id: str, *args, **kwargs):
        if thing_id not in self.storage:
            raise KeyError(f"{thing_id!r} does not exist")
        return func(self, thing_id, *args, **kwargs)

    return decorated_method


class StorageManager:
    def __init__(self, storage: Dict[str, Thing]):
        self.storage = storage
        # maps the names of stores to the ids of things that are in them
        self._stores: Dict[str, List[str]] = defaultdict(list)
        # maps the ids of thing to the names of stores they are in
        self._thing_stores: Dict[str, str] = {}

    def get(self, thing_id: str) -> Optional[Thing]:
        return self.storage.get(thing_id, None)

    def add_store(self, store: Store):
        if store.id in self._stores:
            raise UniqueConstraintError(
                f"store with the id {store.id!r} already exists in this manager"
            )
        self._stores[store.id] = []
        store.set_manager(self)

    @_require_thing_exists
    def add_thing_to_store(self, thing_id: str, store_id: str):
        logger.debug(f"adding {thing_id!r} to store {store_id!r}")
        # first, remove the thing from where it is if it already has a place
        if thing_id in self._thing_stores and self._thing_stores[thing_id]:
            current_store = self._thing_stores[thing_id]
            logger.debug(
                f"{thing_id!r} is currently in {current_store!r}, remove it from there"
            )
            self._stores[current_store].remove(thing_id)
        # now add the thing to the intended store and update the thing's store
        self._stores[store_id].append(thing_id)
        self._thing_stores[thing_id] = store_id

    @_require_thing_exists
    def pop_thing_from_store(self, thing_id: str, store_id: str) -> Optional[Thing]:
        if thing_id in self._stores[store_id]:
            logger.debug(f"removing {thing_id!r} from {store_id!r}")
            self._stores[store_id].remove(thing_id)
            self._thing_stores[thing_id] = None
            return self.storage[thing_id]

    @_require_thing_exists
    def get_thing_from_store(self, thing_id: str, store_id: str) -> Optional[Thing]:
        if thing_id in self._stores[store_id]:
            return self.storage[thing_id]

    def get_things_from_store(self, store_id: str) -> Dict[str, Thing]:
        return {thing_id: self.storage[thing_id] for thing_id in self._stores[store_id]}

    def get_store_id_from_thing(self, thing: Thing) -> Optional[str]:
        return self._thing_stores.get(thing.id)


class Store:
    """things such as the inventory and room.items, room.creatures should be a store and not a dict
    reasoning:
        manage where which item is without copying the items
    """

    def __init__(self, store_id: str, limit: int = None):
        self.id = store_id
        self.limit = limit
        self.manager: StorageManager = None

    def set_manager(self, manager: StorageManager):
        self.manager = manager

    # todo: rename add -> put ?
    def add(self, thing: Thing):
        already_there = self.keys()
        if (
            self.limit is not None
            and thing.id not in already_there
            and len(already_there) == self.limit
        ):
            raise StoreLimitExceededError(
                f"cannot add {thing.id!r} to store {self.id!r}: store is full"
            )
        self.manager.add_thing_to_store(thing.id, self.id)

    def get(self, thing_id: str) -> Optional[Thing]:
        return self.manager.get_thing_from_store(thing_id, self.id)

    def pop(self, thing_id: str) -> Optional[Thing]:
        return self.manager.pop_thing_from_store(thing_id, self.id)

    def items(self, filter: List[Type] = None) -> Dict[str, Thing]:
        things = self.manager.get_things_from_store(self.id)
        if filter:
            return {
                k: v for k, v in things.items() if any(isinstance(v, t) for t in filter)
            }
        return things

    def keys(self, filter: List[Type] = None) -> List[str]:
        return self.items(filter).keys()

    def values(self, filter: List[Type] = None) -> List[Thing]:
        return self.items(filter).values()

    def __contains__(self, other_id) -> bool:
        return other_id in self.keys()


@dataclass
class Item(Thing):
    value: int = 0
    takable: bool = True


@dataclass
class Key(Item):
    key_id: int = 0


@dataclass
class Weapon(Item):
    strength: float = 0
    strength_variation: float = 0

    def calculate_damage(self, random_engine: Random) -> float:
        variation = random_engine.uniform(-1, 1) * self.strength_variation
        return abs(self.strength * (1 - variation))


@dataclass
class Container(Item):
    limit: Optional[int] = None
    _contains: Store = None

    def __post_init__(self):
        self._contains = Store(self.id, limit=self.limit)

    def insert(self, other: Thing):
        self._contains.add(other)

    def pop(self, other_id: str) -> Optional[Thing]:
        return self._contains.pop(other_id)

    def get_contents(self) -> Dict[str, Thing]:
        return self._contains.items()

    def __contains__(self, other_key: str) -> bool:
        return other_key in self._contains


class Behaviour(ABC):
    parameters: List[str] = None

    def __init__(self, switch=True, params: Dict[str, Any] = None):
        for p in self.parameters:
            if p not in params:
                raise ConfigurationError(
                    f"the behaviour {self.__class__} requires {p!r} to be defined"
                )
        self.switch = switch
        self.params = params

    def switch_on(self):
        self.switch = True

    def switch_off(self):
        self.switch = False

    def toggle(self):
        self.switch = not self.switch

    def is_switched_on(self) -> bool:
        return self.switch

    @abstractmethod
    def run(self, creature: Creature, state: State) -> Optional[m]:
        pass


@dataclass
class Creature(Thing):
    dead_description: str = None
    alive: bool = True
    # behaviours could look like this: {"spawn": {"probability": 0.2, "rooms": ["field_0", "field_1"]}}
    behaviours: Dict[str, Behaviour] = field(default_factory=dict)

    def call_behaviour(self, behaviourname: str, state: State) -> Optional[m]:
        if behaviourname not in self.behaviours:
            raise ConfigurationError(
                f"the behaviour {behaviourname!r} is not defined for the Creature {self!r}"
            )
        if self.behaviours[behaviourname].is_switched_on():
            logger.debug(f"call behaviour {behaviourname!r} for creature {self.id!r}")
            return self.behaviours[behaviourname].run(self, state)

    def behave(self, state: State) -> Optional[m]:
        """
        call all functions specified in behaviours with the given parameters
        """
        msg = m()
        for name in self.behaviours:
            msg += self.call_behaviour(name, state)
        return msg

    def die(self):
        self.alive = False
        self.description = self.dead_description or self.description
        for behaviour in self.behaviours.values():
            behaviour.switch_off()


@dataclass
class Monster(Creature):
    strength: float = 0
    strenth_variation: float = 0.0
    health: float = 100
    fight_message: str = None
    win_message: str = None  # when the player wins
    loose_message: str = None  # when the player looses

    def calculate_damage(self, random_engine: Random) -> float:
        # the state's random engine gets passed so that everything
        # is determined by the state's seed
        variation = random_engine.uniform(-1, 1) * self.strenth_variation
        return abs(self.strength * (1 - variation))
