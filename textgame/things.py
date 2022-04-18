from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any, Callable, Optional
from functools import wraps
from collections import defaultdict
from .messages import m
from .registry import behavior_registry
from .exceptions import ConfigurationError, UniqueConstraintError

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
        self._stores: Dict[str, Set[str]] = defaultdict(set)
        # maps the ids of thing to the names of stores they are in
        self._thing_stores: Dict[str, str] = {}
    
    def add_store(self, store: Store):
        if store.id in self._stores:
            raise UniqueConstraintError(f"store with the id {store.id!r} already exists in this manager")
        self._stores[store.id] = set()
        store.set_manager(self)

    @_require_thing_exists
    def add_thing_to_store(self, thing_id: str, store_id: str):
        logger.debug(f"adding {thing_id!r} to store {store_id!r}")
        # first, remove the thing from where it is if it already has a place
        if thing_id in self._thing_stores and self._thing_stores[thing_id]:
            current_store = self._thing_stores[thing_id]
            logger.debug(f"{thing_id!r} is currently in {current_store!r}, remove it from there")
            self._stores[current_store].remove(thing_id)
        # now add the thing to the intended store and update the thing's store
        self._stores[store_id].add(thing_id)
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
        return {
            thing_id: self.storage[thing_id]
            for thing_id in self._stores[store_id]
        }


class Store:
    """things such as the inventory and room.items, room.creatures should be a store and not a dict
    reasoning: 
        manage where which item is without copying the items
    """

    def __init__(self, store_id: str):
        self.id = store_id
        self.manager: StorageManager = None

    def set_manager(self, manager: StorageManager):
        self.manager = manager

    def add(self, thing: Thing):
        self.manager.add_thing_to_store(thing.id, self.id)
    
    def get(self, thing_id: str) -> Optional[Thing]:
        return self.manager.get_thing_from_store(thing_id, self.id)
    
    def pop(self, thing_id: str) -> Optional[Thing]:
        return self.manager.pop_thing_from_store(thing_id, self.id)
    
    def items(self) -> Dict[str, Thing]:
        return self.manager.get_things_from_store(self.id)
    
    def keys(self) -> List[str]:
        return self.manager.get_things_from_store(self.id).keys()
    
    def values(self) -> List[Thing]:
        return self.manager.get_things_from_store(self.id).values()
    
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
    strength: int = 0


@dataclass
class Creature(Thing):
    dead_description: str = None
    alive: bool = True
    # behaviours could look like this: {"spawn": {"probability": 0.2, "rooms": ["field_0", "field_1"]}}
    behaviours: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def call_behaviour(self, behaviourname: str, state):
        if behaviourname not in self.behaviours:
            raise ConfigurationError(f"the behaviour {behaviourname!r} is not defined for the Creature {self!r}")
        params = self.behaviours[behaviourname]
        if behaviourname not in behavior_registry:
            raise ConfigurationError(f"no behaviour {behaviourname!r} is registered")
        behaviour = behavior_registry[behaviourname]
        return behaviour(self, state, **params)

    def behave(self, state):
        """
        call all functions specified in behaviours with the given parameters
        """
        for name in self.behaviours:
            self.call_behaviour(name, state)

    def die(self):
        self.alive = False
        self.description = self.dead_description or self.description

    
@dataclass
class Monster(Creature):
    strength: int = 0

