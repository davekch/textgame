"""
textgame.world
=====================

This module contains only one class, :class:`textgame.world.World` that
holds all rooms, items and monsters, is responsible for spawning
monsters randomly in the rooms and managing daylight.
At initialization you can pass a dict to :class:`textgame.world.World` that's
formatted like this:

.. code-block:: JSON

   {
    "room_id1": {
        "descript": "You're in the great room.",
        "doors": {"south": "room_id2"}
    },
    "room_id2": {
        "descript": "You're in the small room.",
        "doors": {"north": "room_id1"}
    }
   }

The items inside the dict automatically get converted to :class:`textgame.room.Room` objects
and linked to each other according to the ``doors`` dict.
Every argument of :func:`textgame.room.Room.fill_info` can be put as a key-value
pair inside this dict.

The same is true for items, weapons and monsters, see the example.

World has a member called ``storage_room`` of type :class:`textgame.room.Room` that
can be used to put stuff inside that should not be visible for the player.
"""

import logging
logger = logging.getLogger("textgame.world")
logger.addHandler(logging.NullHandler())
import random
from collections import OrderedDict

from textgame.room import Room
from textgame.movable import Item, Weapon, Monster
from textgame.globals import INFO, FIGHTING


class World:
    """
    :param rooms: dict describing all rooms (see above)
    :param items: dict describing all items
    :param weapons: dict describing all weapons
    :param monsters: you guessed it
    :param seed: seed for the random number generator. If ``None``, a random seed is taken
    :type seed: int
    """

    def __init__(self, rooms=None, items=None, weapons=None, monsters=None, seed=None):
        self.rooms = OrderedDict()
        self.items = OrderedDict()
        self.monsters = OrderedDict()
        self.daytime = "day"
        self.time = 0  # increases by one after each step
        self.nighttime = 200
        # dummy room to keep stuff out of the actual world
        self.storage_room = Room("storage")

        # fill stuff
        if rooms:
            self.create_rooms(rooms)
        if items:
            self.create_items(items)
        if weapons:
            self.create_items(weapons, tag="weapons")
        if monsters:
            self.create_items(monsters, tag="monsters")
        self.put_items_in_place()
        self.put_monsters_in_place()

        self.seed = seed if seed else random.randint(0,1000000)
        logger.debug("seeding world with {}".format(self.seed))
        self.random = random.Random()
        self.random.seed(self.seed)


    def create_rooms(self, descriptions):
        """
        create :class:`textgame.room.Room` objects based on description-dict (see above).
        This gets called on initialization if ``rooms`` was provided.
        """
        for ID in descriptions:
            if not ID in self.rooms:
                # create 'empty' room
                self.rooms[ID] = Room(ID)
            else:
                logger.warning("You're trying to add a room with ID {}"
                    " but it's already there".format(ID))
        logger.info("Created rooms")
        self._fill_room_infos(descriptions)
        logger.info("Added room descriptions")


    def _fill_room_infos(self, descriptions):
        for ID,room in self.rooms.items():
            description = descriptions.get(ID)
            if not description:
                logger.warning("Room {} does not have a description".format(ID))

            # replace "doors" and "hiddendoors" dicts to dicts that
            # contain the actual room objects instead of their names
            if "doors" in description:
                description.update(
                    { "doors": self._convert_door_dict(description["doors"]) }
                )
            else:
                logger.warning("Room {} does not have any doors".format(ID))
            if "hiddendoors" in description:
                description.update(
                    { "hiddendoors": self._convert_door_dict(description["hiddendoors"]) }
                )

            # here's where the work is done
            room.fill_info(**description)


    def _convert_door_dict(self, doordict):
        """
        take {dir: roomid} return {dir: roomobj}
        """
        true_doordict = {}
        for dir,ID in doordict.items():
            true_doordict[dir] = self.room(ID)
        return true_doordict


    def room(self, ID):
        """get room by ID.
        If the room is not found, the logger prints an error

        :param ID: room ID

        :rtype: :class:`textgame.room.Room` or ``None``
        """
        result = self.rooms.get(ID)
        if not result:
            logger.error("Room not found: {}".format(ID))
        return result


    def create_items(self, descriptions, tag="items"):
        """
        create :mod:`textgame.movable` ``[Weapon,Item,Monster]`` objects based on description-dict (see above).
        This gets called on initialization if ``weapons,items,monsters`` was provided.

        :param descriptions:
        :type descriptions: dict
        :param tag: can be 'items', 'monsters', 'weapons'
        """
        for ID,description in descriptions.items():
            if tag == "items":
                self.items[ID] = Item(**description)
            elif tag == "weapons":
                self.items[ID] = Weapon(**description)
            elif tag == "monsters":
                self.monsters[ID] = Monster(**description)
        logger.info("Created {}".format(tag))


    def put_items_in_place(self):
        """
        iterate over all items, see if their ``initlocation`` points to a room
        in this world and add it there.
        This is done automatically if the items are passed at initialization
        """
        for item in self.items.values():
            initlocation = self.rooms.get(item.initlocation)
            if initlocation:
                initlocation.add_item(item)
            else:
                logger.warning("Item {}'s initlocation ({}) could not be found".format(item.id, repr(item.initlocation)))
        logger.info("Put items in place")


    def put_monsters_in_place(self):
        """
        iterate over all monsters, see if their ``initlocation`` points to a room
        in this world and add it there.
        This is done automatically if the monsters are passed at initialization
        """
        for monster in self.monsters.values():
            initlocation = self.rooms.get(monster.initlocation)
            if initlocation:
                initlocation.add_monster(monster)
            elif monster.initlocation:
                logger.warning("Monster {}'s initlocation ({}) could not be found".format(monster.id, repr(monster.initlocation)))
        logger.info("Put monsters in place")


    def set_room_restrictions(self, restrictions):
        """
        takes a dict of the following form:

        .. code-block:: python

           {
            "room_ID": {"func": my_func}
           }

        for every ``room_ID``, find the corresponding room and call
        ``set_specials`` with the mapped dict on it.
        See :func:`textgame.room.Room.set_specials` for further reference.
        """
        for roomid,restriction in restrictions.items():
            if not "func" in restriction:
                logger.error("no 'func' defined in restrictions for room {}".format(roomid))
                continue
            self.room(roomid).set_specials(**restriction)


    def update(self, player):
        """
        increase the time, call :func:`textgame.world.World.manage_fight` and
        :func:`textgame.world.World.manage_daylight`

        :rtype: output of ``manage_fight`` and ``manage_daylight`` (str)
        """
        self.time += 1
        logger.debug("time set to {}".format(self.time))
        msg = self.manage_fight(player)
        msg += self.manage_daylight()
        return msg


    def manage_daylight(self):
        """
        check if it's nighttime and turn all rooms dark if yes

        :rtype: a message that night came in or an empty string
        """
        if self.time > self.nighttime and self.daytime == "day":
            self.daytime = "night"
            # turn all rooms to always dark
            for room in self.rooms.values():
                room.dark["always"] = True
            return '\n\n' + INFO.NIGHT_COMES_IN
        return ''


    def spawn_monster(self, location):
        """randomly spawn a monster in location

        the condition for a monster to spawn is:

        - no other monsters in this room
        - random number must be smaller than monster's ``spawn_prob``
        - at least one of the strings in monster's ``spawns_in`` list must be contained in the location's ID
        - monster's ``spawns_at`` must be equal to the current daytime or 'always'
        - monster must not be active already

        :param location: :class:`textgame.room.Room` in which a monster should spawn
        """
        # remove singleencounters / save active monsters in room for later
        active_beast = None
        for id,monster in list(location.monsters.items()):
            if monster.status["active"] and not monster.status["singleencounter"]:
                active_beast = monster
            elif monster.status["active"] and monster.status["singleencounter"]:
                # remove monster from room and set active to False
                location.monsters.pop(id).status["active"] = False

        # only spawn new if room is empty
        if len(location.monsters) == 0:
            for monster in self.monsters.values():
                cond = self.random.random() < monster.spawn_prob and \
                    any([r in location.id for r in monster.spawns_in]) and \
                    (monster.spawns_at == self.daytime or monster.spawns_at == "always") and \
                    not monster.status["active"]
                if cond:
                    location.add_monster(monster)
                    monster.status["active"] = True
                    monster.history = 0
                    logger.debug("Spawned {} in {}".format(monster.id, location.id))
                    break   # spawn no more
        elif active_beast and active_beast.status["harmless"]:
            # TODO: implement behaviour of harmless monsters
            pass


    def manage_fight(self, player):
        """
        if there are active, harmful monsters around, this method checks if the player is
        fighting them and kills the player / the monster, depending on random numbers
        and the monster's strenght

        :rtype: string describing the status of the fight
        """
        msg = ''
        for monsterid,monster in self.monsters.items():
            if monster.status["active"] and not monster.status["harmless"]:
                logger.debug("managing fight with {}".format(monsterid))
                player.status["fighting"] = True
                # player dies if attacked in the dark
                if player.location.dark["now"]:
                    player.status["alive"] = False
                    return '\n'+FIGHTING.DARK_DEATH.format(monster.name)

                if monster.status["alive"] and player.status["alive"]:
                    if monster.status["fighting"]:
                        msg += '\n'+FIGHTING.SURVIVED_ATTACK.format(monster.name)
                    elif monster.history > 1:
                        player.status["alive"] = False
                        msg += '\n'+FIGHTING.IGNORE
                    elif monster.history >= 0:
                        msg += '\n'+FIGHTING.DEFEND_REMINDER.format(monster.name)

                elif not monster.status["alive"]:
                    monster.status["active"] = False
                    player.status["fighting"] = False
                    player.status["trapped"] = False
                    # move monster from monsters to items to make it takable
                    monster.id = monster.name
                    player.location.add_item( player.location.monsters.pop(monsterid) )
                    msg += '\n'+FIGHTING.SUCCESS.format(monster.name)

                if not player.status["alive"]:
                    msg += '\n'+FIGHTING.LOSER.format(monster.name)

                monster.history += 1
                monster.status["fighting"] = False

                return msg
        return ''
