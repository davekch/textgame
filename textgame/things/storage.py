"""
textgame.things.storage
=========================

This module contains classes to manage the location of things.

:class:`StorageManager` holds all Thing instances. It keeps track of each Thing's location (:class:`Store`) by updating a map of Thing-IDs to the ID of the containing Store. It allows each Thing to have only one unique location.

:class:`Store` represents the "location" of Things. It pretends to contain Things by providing methods like ``add(thing: Thing)`` or ``get(thing_id: str) -> Optional[Thing]`` but under the hood it just tells its StoreManager to change the location of the given Thing.

This mechanism ensures that Things cannot appear in two distinct locations:

.. code-block:: python

    >>> from textgame.things import Thing, StorageManager, Store
    >>> 
    >>> thing = Thing(id="thing", description="")
    >>> manager = StorageManager({"thing": thing})
    >>> 
    >>> # create "locations" for things
    >>> store1 = Store("store1")
    >>> store2 = Store("store2")
    >>> 
    >>> # connect the stores to the manager
    >>> manager.add_store(store1)
    >>> manager.add_store(store2)
    >>> 
    >>> # now the stores can be used to host things
    >>> store1.add(thing)
    >>> store1.items()
    {'thing': Thing(id='thing', description='')}
    >>> store2.items()
    {}
    >>> 
    >>> # adding the thing to store2 automatically removes it from store1
    >>> store2.add(thing)
    >>> store2.items()
    {'thing': Thing(id='thing', description='')}
    >>> store1.items()
    {}
    >>> 

The ``things`` attribute of every :class:`textgame.room.Room` is connected to the same :class:`StorageManager`, the ``things_manager`` attribute of :class:`textgame.state.State`.

Finally, :class:`Contains` is a dataclass-mixin for Things that can contain other Things. :class:`textgame.room.Room` and :class:`textgame.things.items.Container` inherit from :class:`Contains`.
"""

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

C = TypeVar("C", bound=Callable)


def _require_thing_exists(func: C) -> C:
    @wraps(func)
    def decorated_method(self: StorageManager, thing_id: str, *args, **kwargs):
        if thing_id not in self.storage:
            return None
        return func(self, thing_id, *args, **kwargs)

    return decorated_method


T = TypeVar("T", bound=Thing)


class StorageManager(Generic[T]):
    """
    contains Thing instances and keeps track of the IDs of the :class:`Store` s that contain them.

    :param storage: dictionary thing.id -> thing
    """

    def __init__(self, storage: Dict[str, T]):
        self.storage = storage
        # maps the names of stores to the ids of things that are in them
        self._stores: Dict[str, List[str]] = defaultdict(list)
        # maps the ids of thing to the names of stores they are in
        self._thing_stores: Dict[str, str] = {}

    @_require_thing_exists
    def get(self, thing_id: str) -> T:
        """return the Thing with ID ``thing_id`` if present"""
        return self.storage[thing_id]

    def add_store(self, store: Store):
        """connect a Store to this manager"""
        if store.id in self._stores:
            raise UniqueConstraintError(
                f"store with the id {store.id!r} already exists in this manager"
            )
        self._stores[store.id] = []
        store._set_manager(self)

    @_require_thing_exists
    def add_thing_to_store(self, thing_id: str, store_id: str):
        """set the containing Store-ID of ``thing_id`` to ``store_id`` if Thing exists"""
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
        """remove Thing with ``thing_id`` from ``store_id`` and return it if present"""
        if thing_id in self._stores[store_id]:
            logger.debug(f"removing {thing_id!r} from {store_id!r}")
            self._stores[store_id].remove(thing_id)
            self._thing_stores.pop(thing_id)
            return self.storage[thing_id]
        return None

    @_require_thing_exists
    def get_thing_from_store(self, thing_id: str, store_id: str) -> Optional[T]:
        """get Thing with ``thing_id`` from ``store_id`` and return it if present"""
        if thing_id in self._stores[store_id]:
            return self.storage[thing_id]
        return None

    def get_things_from_store(self, store_id: str) -> Dict[str, T]:
        """get all things in Store with ``store_id`` and return as a dict"""
        return {thing_id: self.storage[thing_id] for thing_id in self._stores[store_id]}

    def get_store_id_from_thing(self, thing: T) -> Optional[str]:
        """return the ID of the store that contains ``thing``"""
        return self._thing_stores.get(thing.id)


class Store(Generic[T]):
    """
    represents the location of Things

    :param store_id: some ID (must be unique per StorageManager)
    :param limit: don't allow this Store to contain more than ``limit`` Things. Raise
                  :py:exc:`textgame.exceptions.StoreLimitExceededError` if the limit is
                  about to be exceeded
    """

    def __init__(self, store_id: str, limit: int = None):
        self.id = store_id
        self.limit = limit
        # todo: remove type: ignore and add a require_manager decorator
        self.manager: StorageManager[T] = None  # type: ignore

    def _set_manager(self, manager: StorageManager[T]):
        self.manager = manager

    def add(self, thing: T):
        """add ``thing`` to this store and remove it from its previous location"""
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
        """return Thing with ``thing_id`` if in this store"""
        return self.manager.get_thing_from_store(thing_id, self.id)

    def pop(self, thing_id: str) -> Optional[T]:
        """remove Thing with ``thing_id`` from this store and return it if present"""
        return self.manager.pop_thing_from_store(thing_id, self.id)

    def items(self, filter: List[Type[T]] = None) -> Dict[str, T]:
        """return a dict containing the IDs and Things that this store contains.
        if ``filter`` is given, the dict is filtered for Things that inherit from
        any of the Types given in ``filter``
        """
        things = self.manager.get_things_from_store(self.id)
        if filter:
            return {
                k: v for k, v in things.items() if any(isinstance(v, t) for t in filter)
            }
        return things

    def keys(self, filter: List[Type] = None) -> List[str]:
        """return list of IDs of Things this store contains. ``filter`` behaves like in :py:meth:`Store.items`"""
        return list(self.items(filter).keys())

    def values(self, filter: List[Type] = None) -> List[T]:
        """returns list of Things this store contains. ``filter`` behaves like in :py:meth:`Store.items`"""
        return list(self.items(filter).values())

    def __contains__(self, other_id) -> bool:
        return other_id in self.keys()


@dataclass
class Contains(Generic[T]):
    """dataclass mixin for Things that can contain other Things. The Store that contains
    the other Things is accessable via ``Contains.things``.
    """

    limit: Optional[int] = None
    # gets set in post_init
    things: Store[T] = field(default=None, init=False)  # type: ignore

    def __post_init__(self):
        self.things = Store(self.id, limit=self.limit)

    # improve api to have get_thing and add_thing
    def insert(self, other: T):
        """add ``other`` to things"""
        self.things.add(other)

    def pop(self, other_id: str) -> Optional[T]:
        """pop Thing with ``other_id`` from things"""
        return self.things.pop(other_id)

    def get_contents(self) -> Dict[str, T]:
        """return the contained Things as a dict"""
        return self.things.items()

    def __contains__(self, other_key: str) -> bool:
        return other_key in self.things
