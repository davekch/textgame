from __future__ import annotations
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, Any, List, Optional
from random import Random
from .room import Room
from .things import Item, Creature, Lightsource, Store, Thing, StorageManager
from .messages import m

import logging

logger = logging.getLogger("textgame.state")
logger.addHandler(logging.NullHandler())


class PlayerStatus(Enum):
    NORMAL = auto()
    TRAPPED = auto()
    FIGHTING = auto()
    DEAD = auto()


class Daytime(Enum):
    DAY = auto()
    NIGHT = auto()


class EventABC(ABC):
    @abstractmethod
    def condition(self, state: State) -> bool:
        """check if this event should happen"""

    @abstractmethod
    def call(self, state: State) -> Optional[m]:
        """call this event"""


@dataclass
class Event(EventABC):
    when: Callable[[State], bool]
    then: Callable[[State], Optional[m]]

    def condition(self, state: State) -> bool:
        return self.when(state)

    def call(self, state: State) -> bool:
        return self.then(state)


@dataclass
class Timer(EventABC):
    time: int
    then: Callable[[State], Optional[m]]

    def condition(self, state: State) -> bool:
        return state.time >= self.time

    def call(self, state: State) -> bool:
        return self.then(state)


class State:
    def __init__(
        self,
        rooms: Dict[str, Room],
        player_location: Room,
        creatures: Dict[str, Creature] = None,
        # contains mappings of creature.id to room.id
        items: Dict[str, Item] = None,
    ):
        self.rooms = rooms
        self.player_location = player_location
        self.player_location.visit()  # mark the initial room as visited
        # throw creatures and items into the things_manager
        things = {**(items or {}), **(creatures or {})}
        self.things_manager = StorageManager(things)
        # create a store for inventory and register it in the items manager
        inventory = Store("inventory")
        self.things_manager.add_store(inventory)
        self.inventory = inventory
        self.player_status: PlayerStatus = PlayerStatus.NORMAL
        self.player_location_old: Room = None
        self.misc: Dict[str, Any] = {}
        self.score = 0
        self.health = 100
        self.time = 0
        self.events: Dict[str, List[EventABC]] = {"ready": [], "pending": []}
        self.daytime: Daytime = Daytime.DAY
        self.random = Random()

    def lighting(self) -> bool:
        return bool(self.inventory.keys(filter=[Lightsource]))

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def get_location_of(self, thing: Thing) -> Optional[Room]:
        maybe = self.things_manager.get_store_id_from_thing(thing)
        return self.get_room(maybe)

    def set_random_seed(self, seed: int):
        self.random.seed(seed)

    def set_event(self, event: EventABC):
        if event.condition(self):
            self.events["ready"].append(event)
        else:
            self.events["pending"].append(event)

    def pop_ready_events(self) -> List[EventABC]:
        # find all events in pending that are now ready
        for event in self.events["pending"].copy():
            if event.condition(self):
                self.events["pending"].remove(event)
                self.events["ready"].append(event)
        ready = self.events["ready"]
        self.events["ready"] = []
        return ready
