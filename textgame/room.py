from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List, TYPE_CHECKING
from .things import Creature, Item, Lightsource, Store, Thing, _Contains
from .messages import m, DESCRIPTIONS, MOVING, INFO
from .defaults.words import DIRECTIONS
from .registry import roomhook_registry

if TYPE_CHECKING:
    from .state import State

import logging

logger = logging.getLogger("textgame.room")
logger.addHandler(logging.NullHandler())


@dataclass
class Room(_Contains, Thing):
    """
    :param ID: unique identifier
    :param description: string describing the room
    :param shortdescription: string describing the room, but shorter
    :param value: how much player's score increases on first visit
    :type value: int or float
    :param dark: dict specifying if the room is dark. Sould be formatted like ``{"now": <bool>, "always": <bool>}``
    :param sound: string describing the sound in this room
    :param hint: string giving a hint on what to do in this room
    :param hint_value: how much score this hint costs
    :type hint_value: int or float
    :param errors: dict mapping directions to error messages that get printet if player tries to go in this direction eg ``{"north":"Something blocks the way."}``
    :param doors: dict mapping directions to rooms
    :param hiddendoors: dict mapping directions to rooms but it's not possible to use these connections via :func:`textgame.player.Player.go`
    :param locked: dict mapping directions to the state of the connections, eg ``{"north": {"locked":True, "key":123}}`` see examples
    :param dir_descriptions: dict mapping directions to descriptive messages about going in this directions, eg ``{"up": "You spread your wings and start to fly."}``
    """

    shortdescription: str = ""
    value: int = 5
    dark: Dict = field(default_factory=dict)
    sound: str = DESCRIPTIONS.NO_SOUND
    hint: str = ""
    hint_value: int = 2
    errors: Dict[str, str] = field(default_factory=dict)
    doors: Dict[str, str] = field(default_factory=dict)
    hiddendoors: Dict[str, str] = field(default_factory=dict)
    locked: Dict[str, Dict] = field(default_factory=dict)
    dir_descriptions: Dict[str, str] = field(default_factory=dict)
    visited: bool = field(default=False, init=False)

    def __post_init__(self):
        super().__post_init__()
        # fill up all the dicts with missing info
        self.doors.update({dir: None for dir in DIRECTIONS if dir not in self.doors})
        # dict that describes the locked/opened state of doors
        self.locked.update(
            {
                dir: {"locked": False, "key": None}
                for dir in DIRECTIONS
                if dir not in self.locked
            }
        )
        # description to print when going in this direction
        self.dir_descriptions.update(
            {dir: "" for dir in DIRECTIONS if dir not in self.dir_descriptions}
        )
        self.shortdescription = self.shortdescription or self.description
        self.dark = self.dark if self.dark else {"now": False, "always": False}

        # errors is a dict that contains error messages that get printed if player
        # tries to move to a direction where there is no door
        self.errors.update(
            {dir: MOVING.FAIL_CANT_GO for dir in DIRECTIONS if dir not in self.errors}
        )

        for dir, room in self.doors.items():
            self.add_connection(dir, room)

        for dir, room in self.hiddendoors.items():
            self.add_connection(dir, room, hidden=True)

        # validate the locked dict
        if self.locked:
            for dir, lock in self.locked.items():
                if "locked" not in lock or "key" not in lock:
                    logger.warning(
                        f"locked dict of room {self.id} in direction {dir} is badly formatted: {self.locked}"
                    )
                if dir not in DIRECTIONS:
                    logger.warning(
                        f"locked dict of room {self.id}: {id} is not a direction"
                    )

    def add_connection(self, dir: str, room_id: str, hidden=False):
        # todo: remove this method, its unnecessary and confusing (because it adds a string to the doors, not a room)
        """add a single connection to the room

        :param dir: direction, must be in :class:`textgame.globals.DIRECTIONS`
        :param room: :class:str
        :param hidden: specify if the connection is hidden
        """
        if not dir in DIRECTIONS:
            logger.error(
                f"You try to add a connection {dir} to {self.id} but this is not a direction"
            )
        if not hidden:
            self.doors[dir] = room_id
        else:
            self.hiddendoors[dir] = room_id

    def reveal_hiddendoors(self):
        """add all hidden connections to visible connections"""
        logger.debug(
            "revealing hiddendoors in room {} to {}".format(
                self.id, ", ".join([dir for dir in self.hiddendoors])
            )
        )
        self.doors.update(self.hiddendoors)

    def visit(self) -> int:
        """mark this room as visited and return its value"""
        self.visited = True
        return self.value

    def call_hook(self, state: State) -> m:
        if self.id in roomhook_registry:
            logger.debug(f"call roomhook for room {self.id!r}")
            return roomhook_registry[self.id](state) or m()
        return m()

    def is_locked(self, direction: str) -> bool:
        """return ``True`` if the door in ``direction`` is locked"""
        return self.locked.get(direction, {}).get("locked")

    def describe_way_to(self, direction: str) -> m:
        """return content of ``self.dir_descriptions`` (see :func:`textgame.room.Room.fill_info`) in the given direction.
        Returns an empty string if no description exists.
        """
        return m(self.dir_descriptions.get(direction, ""))

    def get_connection(self, direction: str) -> Optional[Room]:
        """returns room object that lies in the given direction, ``None`` if there is no door in that direction."""
        return self.doors.get(direction)

    def is_dark(self) -> bool:
        return self.dark["now"] and not self.things.keys(filter=[Lightsource])

    def describe(self, long: bool = False, light: bool = False) -> m:
        long = long or not self.visited
        # if the room is dark, only give the description if there is light
        if self.is_dark() and not light:
            return DESCRIPTIONS.DARK_L

        descript = m(self.description) if long else m(self.shortdescription)
        for thing in self.things.values():
            descript += thing.describe()
        return descript

    def describe_error(self, direction: str) -> m:
        """return content of ``self.errors`` (see :func:`textgame.room.Room.fill_info`) in the given direction. Returns the default
        :attr:`textgame.globals.MOVING.FAIL_CANT_GO` if no other direction is given.
        """
        return m(self.errors[direction])

    def connects_to(self, other: str) -> bool:
        """
        returns ``True`` if there is a connection to other location
        """
        return other in self.doors.values()

    def has_connection_in(self, direction: str, include_hidden: bool = False) -> bool:
        """
        returns ``True`` if there is a connection in the specified direction
        """
        if not include_hidden:
            return self.doors.get(direction) is not None
        else:
            return (
                self.doors.get(direction) is not None
                or self.hiddendoors.get(direction) is not None
            )

    def get_open_connections(self, include_hidden: bool = False) -> Dict[str, Room]:
        return {
            direction: self.doors[direction]
            for direction in DIRECTIONS
            if self.has_connection_in(direction, include_hidden=include_hidden)
            and not self.is_locked(direction)
        }

    def get_door_code(self, direction: str) -> Optional[int]:
        """gets the key code to the door in the given direction, ``None`` else"""
        return self.locked.get(direction, {}).get("key")

    def set_locked(self, direction: str, locked: bool):
        """set the status of the door in ``direction``.

        :param direction: one of :data:`textgame.globals.DIRECTIONS`
        :type direction: string
        :param locked: bool
        """
        self.locked[direction]["locked"] = locked

    def get_hint(self) -> Tuple[m, m]:
        """return a tuple of warning and the actual hint (``(m, m)``)"""
        return (INFO.HINT_WARNING.format(self.hint_value), m(self.hint))
