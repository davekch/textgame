from __future__ import annotations
from collections import defaultdict
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
        self.timed_events: defaultdict[
            int, List[Callable[[State], Optional[m]]]
        ] = defaultdict(list)
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

    def set_timer(self, time: int, callback: Callable[[State], m]):
        """set a callback function to be run after the internal clock has ticked `time` steps.
        only makes sense if textgame.defaults.hooks.time and textgame.defaults.hooks.timers is enabled
        """
        self.timed_events[self.time + time].append(callback)

    def pop_timers(self) -> List[Callable[[State], m]]:
        """get a list of callback functions that should be run now"""
        return self.timed_events.pop(self.time, [])

    def pop_missed_timers(self) -> List[Callable[[State], m]]:
        """get dict of times and callbacks that were missed"""
        missed = []
        for time in list(self.timed_events.keys()):
            if time < self.time:
                missed.extend(self.timed_events.pop(time), [])
        return missed
