from __future__ import annotations
from dataclasses import dataclass, field
from functools import wraps
from collections import defaultdict
from typing import (
    Callable,
    Generic,
    List,
    Dict,
    Optional,
    Type,
    TypeVar,
)
from .base import Thing
from ..exceptions import (
    UniqueConstraintError,
    StoreLimitExceededError,
)

import logging

logger = logging.getLogger("textgame.things")
logger.addHandler(logging.NullHandler())


def _require_thing_exists(func: Callable) -> Callable:
    @wraps(func)
    def decorated_method(self: StorageManager, thing_id: str, *args, **kwargs):
        if thing_id not in self.storage:
            return None
        return func(self, thing_id, *args, **kwargs)

    return decorated_method


T = TypeVar("T", bound=Thing)


class StorageManager(Generic[T]):
    def __init__(self, storage: Dict[str, T]):
        self.storage = storage
        # maps the names of stores to the ids of things that are in them
        self._stores: Dict[str, List[str]] = defaultdict(list)
        # maps the ids of thing to the names of stores they are in
        self._thing_stores: Dict[str, str] = {}

    @_require_thing_exists
    def get(self, thing_id: str) -> T:
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
    def pop_thing_from_store(self, thing_id: str, store_id: str) -> Optional[T]:
        if thing_id in self._stores[store_id]:
            logger.debug(f"removing {thing_id!r} from {store_id!r}")
            self._stores[store_id].remove(thing_id)
            self._thing_stores.pop(thing_id)
            return self.storage[thing_id]
        return None

    @_require_thing_exists
    def get_thing_from_store(self, thing_id: str, store_id: str) -> Optional[T]:
        if thing_id in self._stores[store_id]:
            return self.storage[thing_id]
        return None

    def get_things_from_store(self, store_id: str) -> Dict[str, T]:
        return {thing_id: self.storage[thing_id] for thing_id in self._stores[store_id]}

    def get_store_id_from_thing(self, thing: T) -> Optional[str]:
        return self._thing_stores.get(thing.id)


class Store(Generic[T]):
    """things such as the inventory and room.items, room.creatures should be a store and not a dict
    reasoning:
        manage where which item is without copying the items
    """

    def __init__(self, store_id: str, limit: int = None):
        self.id = store_id
        self.limit = limit
        # todo: remove type: ignore and add a require_manager decorator
        self.manager: StorageManager[T] = None  # type: ignore

    def set_manager(self, manager: StorageManager[T]):
        self.manager = manager

    # todo: rename add -> put ?
    def add(self, thing: T):
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

    def get(self, thing_id: str) -> Optional[T]:
        return self.manager.get_thing_from_store(thing_id, self.id)

    def pop(self, thing_id: str) -> Optional[T]:
        return self.manager.pop_thing_from_store(thing_id, self.id)

    def items(self, filter: List[Type[T]] = None) -> Dict[str, T]:
        things = self.manager.get_things_from_store(self.id)
        if filter:
            return {
                k: v for k, v in things.items() if any(isinstance(v, t) for t in filter)
            }
        return things

    def keys(self, filter: List[Type] = None) -> List[str]:
        return list(self.items(filter).keys())

    def values(self, filter: List[Type] = None) -> List[T]:
        return list(self.items(filter).values())

    def __contains__(self, other_id) -> bool:
        return other_id in self.keys()


@dataclass
class _Contains:
    limit: Optional[int] = None
    # gets set in post_init
    things: Store = field(default=None, init=False)  # type: ignore

    def __post_init__(self):
        self.things = Store(self.id, limit=self.limit)

    # improve api to have get_thing and add_thing
    def insert(self, other: Thing):
        self.things.add(other)

    def pop(self, other_id: str) -> Optional[Thing]:
        return self.things.pop(other_id)

    def get_contents(self) -> Dict[str, Thing]:
        return self.things.items()

    def __contains__(self, other_key: str) -> bool:
        return other_key in self.things
