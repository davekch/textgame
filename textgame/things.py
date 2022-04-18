from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from random import Random
from typing import List, Dict, Callable, Optional, Type
from functools import wraps
from collections import defaultdict
from .messages import m
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
    description: str

    def describe(self) -> m:
        return m(self.description)


@dataclass
class Movable(Thing):
    name: str
    initlocation: str


def _require_thing_exists(func: Callable) -> Callable:
    @wraps(func)
    def decorated_method(self: StorageManager, thing_id: str, *args, **kwargs):
        if thing_id not in self.storage:
            return None
        return func(self, thing_id, *args, **kwargs)

    return decorated_method


class StorageManager:
    def __init__(self, storage: Dict[str, Thing]):
        self.storage = storage
        # maps the names of stores to the ids of things that are in them
        self._stores: Dict[str, List[str]] = defaultdict(list)
        # maps the ids of thing to the names of stores they are in
        self._thing_stores: Dict[str, str] = {}

    @_require_thing_exists
    def get(self, thing_id: str) -> Thing:
        return self.storage[thing_id]

    def add_store(self, store: Store):
        if store.id in self._stores:
            raise UniqueConstraintError(
                f"store with the id {store.id!r} already exists in this manager"
            )
        self._stores[store.id] = []
        store.set_manager(self)

    @_require_thing_exists
    def add_thing_to_store(self, thing_id: str, store_id: str):
        # first, remove the thing from where it is if it already has a place
        if thing_id in self._thing_stores and self._thing_stores[thing_id]:
            current_store = self._thing_stores[thing_id]
            logger.debug(
                f"{thing_id!r} is currently in {current_store!r}, remove it from there"
            )
            self._stores[current_store].remove(thing_id)
        # now add the thing to the intended store and update the thing's store
        logger.debug(f"adding {thing_id!r} to store {store_id!r}")
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
class Takable:
    takable: bool = True


@dataclass
class Item(Takable, Movable):
    value: int = 0


class Lightsource(Item):
    pass


@dataclass
class Key(Item):
    key_id: int = 0


@dataclass
class _HasStrength:
    strength: float = 0
    strength_variation: float = 0

    def calculate_damage(self, random_engine: Random) -> float:
        # the state's random engine gets passed so that everything
        # is determined by the state's seed
        variation = random_engine.uniform(-1, 1) * self.strength_variation
        return abs(self.strength * (1 - variation))


@dataclass
class Weapon(_HasStrength, Item):
    pass


@dataclass
class _Contains:
    limit: Optional[int] = None
    things: Store = field(default=None, init=False)

    def __post_init__(self):
        self.things = Store(self.id, limit=self.limit)

    def insert(self, other: Thing):
        self.things.add(other)

    def pop(self, other_id: str) -> Optional[Thing]:
        return self.things.pop(other_id)

    def get_contents(self) -> Dict[str, Thing]:
        return self.things.items()

    def __contains__(self, other_key: str) -> bool:
        return other_key in self.things


@dataclass
class Container(_Contains, Item):
    pass


@dataclass
class Behaviour(ABC):
    switch: bool
    # note: switch gets a default of True by loader.behaviour_factory if nothing
    # else is set. this is ugly but necessary because default-values in dataclass
    # base classes mess up inheritance. when updating to python3.10, use
    # @dataclass(kw_only=True) instead

    def switch_on(self):
        self.switch = True

    def switch_off(self):
        self.switch = False

    def toggle(self):
        if self.is_switched_on():
            self.switch_off()
        else:
            self.switch_on()

    def is_switched_on(self) -> bool:
        return self.switch

    @abstractmethod
    def run(self, creature: Creature, state: State) -> Optional[m]:
        pass


def behavioursequence(behaviours: List[Type[Behaviour]]) -> Type[Behaviour]:
    """create a behaviour that runs each of the behaviours one after another"""

    @dataclass
    class CombinedBehaviour(*behaviours, Behaviour):
        def __post_init__(self):
            # this must be a post-init because we must not overwrite the init by the behaviours
            # initialize each behaviour
            self.behaviours: List[Behaviour] = []
            for behaviour in behaviours:
                # collect the parameters that are meant for this behaviour
                parameters = {
                    field.name: getattr(self, field.name)
                    for field in fields(behaviour)
                    if field.init
                }
                self.behaviours.append(behaviour(**parameters))

        def run(self, creature: Creature, state: State) -> m:
            for behaviour in self.behaviours:
                if behaviour.is_switched_on():
                    msg = behaviour.run(creature, state)
                    break
            else:
                # no break, this means all behaviours are switched off
                self.switch_off()
                msg = m()
            return msg

        def switch_on(self):
            super().switch_on()
            for behaviour in self.behaviours:
                behaviour.switch_on()

        def switch_off(self):
            super().switch_off()
            for behaviour in self.behaviours:
                behaviour.switch_off()

    return CombinedBehaviour


@dataclass
class _CanDie:
    dead_description: str = None
    alive: bool = True

    def die(self):
        self.alive = False
        self.description = self.dead_description or self.description


@dataclass
class _Behaves:
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


@dataclass
class Creature(_CanDie, _Behaves, Movable):
    def die(self):
        super().die()
        for behaviour in self.behaviours.values():
            behaviour.switch_off()


@dataclass
class _CanFight(_HasStrength):
    health: float = 100
    fight_message: str = None
    win_message: str = None  # when the player wins
    loose_message: str = None  # when the player looses


@dataclass
class Monster(_CanFight, Creature):
    pass


@dataclass
class TakableMonster(Takable, Monster):
    takable = False

    def die(self):
        self.takable = True
        return super().die()
