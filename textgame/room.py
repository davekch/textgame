"""
textgame.room
=====================

This module contains only one class, :class:`textgame.room.Room`, that represents
a single room and its connections to other rooms.

You can create one like so

.. code-block:: python

   myroom1 = textgame.room.Room("room_01")
   myroom2 = textgame.room.Room("room_02")
   # add some information
   myroom1.fill_info(
       doors={"north": myroom2},
       descript="You are at a beach stretching from north to south.",
       sdescript="You're at the beach."
   )

See :func:`textgame.room.Room.fill_info` for more. It is also possible for a room to
have a connection to itself.

``Room`` has a method :func:`textgame.room.Room.check_restrictions` that checks if
it's dark inside the room and calls a ``special_func``. You can specify the ``special_func``
to do whatever you wish should happen when a player enters this room. Say for example,
all the player's money gets stolen if he/she enters ``myroom2``:

.. code-block:: python

   # NOTE: the first argument must be the player
   def steal_money(player):
       if "money" in player.inventory:
           # don't delete the money, better store it in
           # the storage room (see :class:`textgame.world.World`)
           player.world.storage_room.add_item(player.pop_item("money"))
           return "Someone just stole all your money."
        # be sure to return a string
        return ""

    myroom2.set_specials(steal_money)
"""

import logging
logger = logging.getLogger("textgame.room")
logger.addHandler(logging.NullHandler())

from textgame.globals import MOVING, DESCRIPTIONS, INFO, DIRECTIONS, LIGHT


class Room:
    """
    :param ID: unique identifier
    :type ID: str
    """

    def __init__(self, ID):
        self.id = ID   # unique, similar rooms should have a common keyword in ID
        self.doors = {}
        # dict that describes the locked/opened state of doors
        self.locked = {}
        # description to print when going in this direction
        self.dir_descriptions = {}
        # errors is a dict that contains error messages that get printed if player
        # tries to move to a direction where there is no door
        self.errors = {}
        # items that lie around in this room, format {ID: item}
        self.items = {}
        # monsters that are in this room, format {ID: monster}
        self.monsters = {}
        self.visited = False
        self.hiddendoors = {}
        # special_func gets called on Room.check_restrictions
        # which is called when the player enters the room
        self.special_func = None
        self.special_args = {}
        # initialize descriptive information
        self.fill_info()


    def fill_info(self, descript="", sdescript="", value=5,\
                  dark=None, sound=DESCRIPTIONS.NO_SOUND,\
                  hint="", hint_value=2, errors=None,\
                  doors=None, hiddendoors=None, locked=None, dir_descriptions=None):
        """add all the descriptive information

        :param descript: string describing the room
        :param sdescript: string describing the room, but shorter
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
        self.description = descript
        self.shortdescription = sdescript
        self.value = value
        self.dark = dark if dark else {"now": False, "always": False}
        self.sound = sound
        self.hint = hint
        self.hint_value = hint_value

        if errors:
            for dir in errors:
                if dir not in DIRECTIONS:
                    logger.warning("In errors of room {}: {} is not"
                                   " a direction".format(self.id, dir))
            self.errors.update(errors)

        if doors:
            for dir,room in doors.items():
                self.add_connection(dir, room)

        if hiddendoors:
            for dir,room in hiddendoors.items():
                self.add_connection(dir, room, hidden=True)

        if locked:
            for dir,lock in locked.items():
                if "closed" not in lock or "key" not in lock:
                    logger.warning("locked dict of room {} in direction {} is "
                        "badly formatted".format(self.id, dir))
                if dir not in DIRECTIONS:
                    logger.warning("locked dict of room {}: {} is not a direction".format(self.id, dir))
            self.locked.update(locked)

        if dir_descriptions:
            for dir in dir_descriptions:
                if dir not in DIRECTIONS:
                    logger.warning("dir_descriptions dict of room {}: {} is not a direction".format(self.id, dir))
            self.dir_descriptions.update(dir_descriptions)


    def describe(self, long=False):
        """
        return the description (``long=True``) or short description (``long=False``)
        of the room or :class:`textgame.globals.DESCRIPTIONS.DARK_L` if the room is dark
        """
        long = long or not self.visited
        if self.dark["now"]:
            return DESCRIPTIONS.DARK_L
        descript = self.description if long else self.shortdescription
        for item in self.items.values():
            descript += "\n" + item.describe()
        for monster in self.monsters.values():
            descript += "\n" + monster.describe()
        return descript


    def add_connection(self, dir, room, hidden=False):
        """add a single connection to the room

        :param dir: direction, must be in :data:`textgame.globals.DIRECTIONS`
        :param room: :class:`textgame.room.Room` object
        :param hidden: specify if the connection is hidden
        """
        if not dir in DIRECTIONS:
            logger.error("You try to add a connection {} to {} "
                "but this is not a direction".format(dir, self.id))
        if not hidden:
            self.doors[dir] = room
        else:
            self.hiddendoors[dir] = room


    def visit(self):
        """mark this room as visited if it's not dark and return its value
        """
        if not self.dark["now"]:
            self.visited = True
            return self.value
        return 0


    def is_locked(self, direction):
        """return ``True`` if the door in ``direction`` is locked
        """
        return self.locked.get(direction, {}).get("closed")


    def describe_way_to(self, direction):
        """return content of ``self.dir_descriptions`` (see :func:`textgame.room.Room.fill_info`) in the given direction.
        Returns an empty string if no description exists.
        """
        return self.dir_descriptions.get(direction, "")


    def get_connection(self, direction):
        """returns room object that lies in the given direction, ``None`` if there is no door in that direction.
        """
        return self.doors.get(direction)


    def is_dark(self):
        return self.dark["now"]


    def describe_error(self, direction):
        """return content of ``self.errors`` (see :func:`textgame.room.Room.fill_info`) in the given direction. Returns the default
        :attr:`textgame.globals.MOVING.FAIL_CANT_GO` if no other direction is given.
        """
        error = self.errors.get(direction)
        if not error:
            return MOVING.FAIL_CANT_GO
        return error


    def connects_to(self, other):
        """
        returns ``True`` if there is a connection to other location
        """
        return other in self.doors.values()


    def has_connection_in(self, direction):
        """
        returns ``True`` if there is a connection in the specified direction
        """
        return self.doors.get(direction) is not None


    def get_door_code(self, direction):
        """gets the key code to the door in the given direction, ``None`` else
        """
        return self.locked.get(direction, {}).get("key")


    def set_locked(self, direction, locked):
        """set the status of the door in ``direction``.

        :param direction: one of :data:`textgame.globals.DIRECTIONS`
        :type direction: string
        :param locked: bool
        """
        self.locked[direction]["closed"] = locked


    def get_hint(self):
        """return a tuple of warning and the actual hint (``(str,str)``)
        """
        return (INFO.HINT_WARNING.format(self.hint_value), self.hint)


    def has_light(self):
        """returns true if there's anything inside room that lights it up
        """
        return any([lamp in self.items for lamp in LIGHT])


    def set_specials(self, func, **kwargs):
        """set a custom function that gets called in :func:`textgame.room.Room.check_restrictions`

        :param func: function that takes a :class:`textgame.player.Player` object as first argument. Must return a string!
        :param kwargs: optional keyword arguments for ``func``
        """
        self.special_func = func
        self.special_args = kwargs if kwargs else {}


    def check_restrictions(self, player):
        """check if it's dark and call the function set by :func:`textgame.room.Room.set_specials`

        :param player: :class:`textgame.player.Player` object
        :returns: empty string or the string returned by the special function
        """
        self.dark["now"] = self.dark["always"] and not (self.has_light() or player.has_light())
        if self.special_func:
            return self.special_func(player, **self.special_args)
        return ""


    def reveal_hiddendoors(self):
        """add all hidden connections to visible connections
        """
        logger.debug("revealing hiddendoors in room {} to {}"\
            .format(self.id, ", ".join([dir for dir in self.hiddendoors])))
        self.doors.update(self.hiddendoors)


    def add_item(self, item):
        """put an item inside the room
        """
        if item.id not in self.items:
            self.items[item.id] = item
        else:
            logger.warning("You try to add item {} to room {} but "\
                "it's already there".format(item.id, self.id))


    def get_item(self, item_id):
        return self.items.get(item_id)


    def pop_item(self, item_id):
        return self.items.pop(item_id)


    def get_itemnames(self):
        return list(self.items.keys())


    def add_monster(self, monster):
        """put a monster inside the room
        """
        if monster.id not in self.monsters:
            self.monsters[monster.id] = monster
        else:
            logger.warning("You try to add monster {} to room {} but "\
                "it's already there".format(monster.id, self.id))
