from __future__ import annotations
from enum import Enum, auto
from typing import Dict, Any, Optional
from random import Random
from .room import Room
from .things import Item, Creature, Store, Thing, StorageManager

import logging
logger = logging.getLogger("textgame.state")
logger.addHandler(logging.NullHandler())


class PlayerStatus(Enum):
    NORMAL = auto()
    TRAPPED = auto()
    FIGHTING = auto()
    DEAD = auto()


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
        self.creatures = StorageManager(creatures)  # rename to creature_manager and item_manager?
        self.items = StorageManager(items)
        # create a store for inventory and register it in the items manager
        inventory = Store("inventory")
        self.items.add_store(inventory)
        self.inventory = inventory
        self.player_status: PlayerStatus = PlayerStatus.NORMAL
        self.player_location_old: Room = None
        self.misc: Dict[str, Any] = {}
        self.score = 0
        self.time = 0
        self.random = Random()

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)
    
    def get_location_of(self, thing: Thing) -> Optional[Room]:
        room_id = self.items.get_store_id_from_thing(thing) or self.creatures.get_store_id_from_thing(thing)
        return self.get_room(room_id)
    
    def set_random_seed(self, seed: int):
        self.random.seed(seed)
