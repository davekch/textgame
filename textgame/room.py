from typing import Dict, Optional, Tuple, List
from .messages import m, DESCRIPTIONS, MOVING, INFO
from .things import Creature, Item
from .defaults.words import DIRECTIONS

import logging
logger = logging.getLogger("textgame.room")
logger.addHandler(logging.NullHandler())


class Room:
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

    def __init__(self,
        ID: str,
        description: str,
        shortdescription: str = "",
        value: int = 5,
        dark: Dict = None,
        sound: str = DESCRIPTIONS.NO_SOUND,
        hint: str = "",
        hint_value: int = 2,
        errors: Dict[str, str] = None,
        doors: Dict[str, str] = None,
        hiddendoors: Dict[str, str] = None,
        locked: Dict[str, Dict] = None,
        dir_descriptions: Dict[str, str] = None
    ):
        self.id = ID   # unique, similar rooms should have a common keyword in ID
        self.doors = {dir: None for dir in DIRECTIONS}
        # dict that describes the locked/opened state of doors
        self.locked = {dir: {"closed":False, "key":None} for dir in DIRECTIONS}
        # description to print when going in this direction
        self.dir_descriptions = {dir: m() for dir in DIRECTIONS}
        # items that lie around in this room, format {ID: item}
        self.items = {}
        # monsters that are in this room, format {ID: monster}
        self.creatures = {}
        self.visited = False
        self.hiddendoors = {}
        self.description = m(description)
        self.shortdescription = m(shortdescription) or self.description
        self.value = value
        self.dark = dark if dark else {"now": False, "always": False}
        self.sound = m(sound)
        self.hint = m(hint)
        self.hint_value = hint_value

        # errors is a dict that contains error messages that get printed if player
        # tries to move to a direction where there is no door
        self.errors = {dir: MOVING.FAIL_CANT_GO for dir in DIRECTIONS}
        if errors:
            for dir in errors:
                if dir not in DIRECTIONS:
                    logger.warning(
                        f"In errors of room {self.id}: {dir} is not a direction".format(self.id, dir)
                    )
            self.errors.update(errors)

        if doors:
            for dir,room in doors.items():
                self.add_connection(dir, room)

        if hiddendoors:
            for dir,room in hiddendoors.items():
                self.add_connection(dir, room, hidden=True)

        if locked:
            for dir,lock in locked.items():
                if "locked" not in lock or "key" not in lock:
                    logger.warning(f"locked dict of room {self.id} in direction {dir} is badly formatted")
                if dir not in DIRECTIONS:
                    logger.warning(f"locked dict of room {self.id}: {id} is not a direction")
            self.locked.update(locked)

        if dir_descriptions:
            for dir in dir_descriptions:
                if dir not in DIRECTIONS:
                    logger.warning("dir_descriptions dict of room {self.id}: {dir} is not a direction")
            self.dir_descriptions.update(dir_descriptions)

    def add_connection(self, dir: str, room_id: str, hidden=False):
        """add a single connection to the room

        :param dir: direction, must be in :class:`textgame.globals.DIRECTIONS`
        :param room: :class:str
        :param hidden: specify if the connection is hidden
        """
        if not dir in DIRECTIONS:
            logger.error(f"You try to add a connection {dir} to {self.id} but this is not a direction")
        if not hidden:
            self.doors[dir] = room_id
        else:
            self.hiddendoors[dir] = room_id

    def describe(self, long=False) -> m:
        """
        return the description (``long=True``) or short description (``long=False``)
        of the room or :class:`textgame.globals.DESCRIPTIONS.DARK_L` if the room is dark
        """
        long = long or not self.visited
        if self.dark["now"]:
            return DESCRIPTIONS.DARK_L
        descript = self.description if long else self.shortdescription
        for item in self.items.values():
            descript += item.describe()
        for monster in self.creatures.values():
            descript += monster.describe()
        return descript

    def visit(self) -> int:
        """mark this room as visited if it's not dark and return its value
        """
        if not self.dark["now"]:
            self.visited = True
            return self.value
        return 0

    def is_locked(self, direction: str) -> bool:
        """return ``True`` if the door in ``direction`` is locked
        """
        return self.locked.get(direction, {}).get("locked")

    def describe_way_to(self, direction: str) -> m:
        """return content of ``self.dir_descriptions`` (see :func:`textgame.room.Room.fill_info`) in the given direction.
        Returns an empty string if no description exists.
        """
        return self.dir_descriptions.get(direction, m())

    def get_connection(self, direction):
        """returns room object that lies in the given direction, ``None`` if there is no door in that direction.
        """
        return self.doors.get(direction)

    def is_dark(self) -> bool:
        return self.dark["now"]

    def describe_error(self, direction: str) -> m:
        """return content of ``self.errors`` (see :func:`textgame.room.Room.fill_info`) in the given direction. Returns the default
        :attr:`textgame.globals.MOVING.FAIL_CANT_GO` if no other direction is given.
        """
        return self.errors[direction]

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
            return self.doors.get(direction) is not None or self.hiddendoors.get(direction) is not None

    def get_door_code(self, direction: str) -> Optional[int]:
        """gets the key code to the door in the given direction, ``None`` else
        """
        return self.locked.get(direction, {}).get("key")

    def set_locked(self, direction: str, locked: bool):
        """set the status of the door in ``direction``.

        :param direction: one of :data:`textgame.globals.DIRECTIONS`
        :type direction: string
        :param locked: bool
        """
        self.locked[direction]["locked"] = locked

    def get_hint(self) -> Tuple[m, int]:
        """return a tuple of warning and the actual hint (``(str,str)``)
        """
        return (INFO.HINT_WARNING.format(self.hint_value), self.hint)

    def add_item(self, item: Item):
        """put an item inside the room
        """
        if item.id not in self.items:
            self.items[item.id] = item
        else:
            logger.warning(f"You try to add item {item.id!r} to room {self.id} but it's already there")

    def get_item(self, item_id: str) -> Item:
        return self.items.get(item_id)

    def pop_item(self, item_id: str) -> Item:
        return self.items.pop(item_id, None)

    def get_itemnames(self) -> List[str]:
        return list(self.items.keys())
    
    def add_creature(self, creature: Creature):
        if creature.id not in self.creatures:
            self.creatures[creature.id] = creature
        else:
            logger.warning(f"You try to add monster {creature.id!r} to room {self.id} but it's already there")
    
    def get_creature(self, creature_id: str) -> Creature:
        return self.creatures.get(creature_id)
    
    def pop_creature(self, creature_id: str) -> Creature:
        return self.creatures.pop(creature_id, None)

