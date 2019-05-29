import logging
logger = logging.getLogger("textgame.world")
logger.addHandler(logging.NullHandler())
import random

from textgame.room import Room
from textgame.movable import Item, Weapon, Monster
from textgame.globals import INFO, FIGHTING


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
            elif monster.initlocation:
                logger.warning("Monster {}'s initlocation ({}) could not be found".format(monster.id, repr(monster.initlocation)))
        logger.info("Put monsters in place")


    def set_room_restrictions(self, restrictions):
        for roomid,restriction in restrictions.items():
            if not "func" in restriction:
                logger.error("no 'func' defined in restrictions for room {}".format(roomid))
                continue
            self.room(roomid).set_specials(**restriction)


    def update(self, player):
        """upate world's status
        """
        self.time += 1
        logger.debug("time set to {}".format(self.time))
        msg = self.manage_fight(player)
        msg += self.manage_daylight()
        return msg


    def manage_daylight(self):
        if self.time > self.nighttime and self.daytime == "day":
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
                    monster.history = 0
                    logger.debug("Spawned {} in {}".format(monster.id, location.id))
                    break   # spawn no more
        elif active_beast and active_beast.status["harmless"]:
            # TODO: implement behaviour of harmless monsters
            pass


    def manage_fight(self, player):
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
