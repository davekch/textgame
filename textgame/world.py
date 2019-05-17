import logging
logger = logging.getLogger(__name__)
import random

from textgame.room import Room
from textgame.movable import Item, Weapon, Monster
from textgame.globals import INFO


class World:
    """
    holds all rooms, items and monsters, is responsible for daylight and spawning
    """

    def __init__(self, rooms=None, items=None, weapons=None, monsters=None):
        self.rooms = {}
        self.items = {}
        self.monsters = {}
        self.daytime = "day"
        self.time = 0  # increases by one after each step

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


    def create_rooms(self, descriptions):
        """
        create Room objects based on descriptions
        this also sets up connections between the rooms (if given in descriptions)
        """
        for ID in descriptions:
            if not ID in self.rooms:
                # create 'empty' room
                self.rooms[ID] = Room(ID)
            else:
                logger.warning("You're trying to add a room with ID {}"
                    " but it's already there".format(ID))
        logger.info("Created rooms")
        self.fill_room_infos(descriptions)
        logger.info("Added room descriptions")


    def fill_room_infos(self, descriptions):
        for ID,room in self.rooms.items():
            description = descriptions.get(ID)
            if not description:
                logger.warning("Room {} does not have a description".format(ID))

            # replace "doors" and "hiddendoors" dicts to dicts that
            # contain the actual room objects instead of their names
            if "doors" in description:
                description.update(
                    { "doors": self.convert_door_dict(description["doors"]) }
                )
            else:
                logger.warning("Room {} does not have any doors".format(ID))
            if "hiddendoors" in description:
                description.update(
                    { "hiddendoors": self.convert_door_dict(description["hiddendoors"]) }
                )

            # here's where the work is done
            room.fill_info(**description)


    def convert_door_dict(self, doordict):
        """
        take {dir: roomid} return {dir: roomobj}
        """
        true_doordict = {}
        for dir,ID in doordict.items():
            true_doordict[dir] = self.room(ID)
        return true_doordict


    def room(self, ID):
        result = self.rooms.get(ID)
        if not result:
            logger.error("Room not found: {}".format(ID))
        return result


    def create_items(self, descriptions, tag="items"):
        """
        create item objects based on descritions
        tag can be items, weapons, monsters
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
        iterate over all items and add them to their initlocation
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
        iterate over all monsters and add them to their initlocation
        """
        for monster in self.monsters.values():
            initlocation = self.rooms.get(monster.initlocation)
            if initlocation:
                initlocation.add_monster(monster)
            else:
                logger.warning("Monster {}'s initlocation ({}) could not be found".format(monster.id, repr(monster.initlocation)))
        logger.info("Put monsters in place")


    def update(self):
        """upate world's status
        """
        self.time += 1
        return self.manage_daylight()


    def manage_daylight(self):
        if self.time > 20 and self.daytime == "day":
            self.daytime = "night"
            # turn all rooms to always dark
            for room in self.rooms.values():
                room.dark["always"] = True
            return '\n\n' + INFO.NIGHT_COMES_IN
        return ''


    def spawn_monster(self, location):
        """randomly spawn a monster in location
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
                cond = random.random() < monster.spawn_prob and \
                    any([r in location.id for r in monster.spawns_in]) and \
                    (monster.spawns_at == self.daytime or monster.spawns_at == "always") and \
                    not monster.status["active"]
                if cond:
                    location.add_monster(monster)
                    monster.status["active"] = True
                    logger.debug("Spawned {} in {}".format(monster.id, location.id))
        elif active_beast and active_beast.status["harmless"]:
            # TODO: implement behaviour of harmless monsters
            pass
