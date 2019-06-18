"""
textgame.movable
=====================

This module is for everything that sits around in rooms.
"""

import logging
logger = logging.getLogger("textgame.movable")
logger.addHandler(logging.NullHandler())


class Item:
    """
    everything that is somewhat movable like treasures, weapons, tools, monsters

    :param description: string describing the thing
    :param name: short name for the thing
    :param ID: unique string by which the item can be taken by the player (eg. 'coins' for 'a sack of coins')
    :param takable: is the player able to add this to his/her inventory?
    :type takable: bool
    :param value: how valuable the item is
    :type value: int or float
    :param key: if an item has a key, it can be used to open/close doors that are locked with the same key
    :param initlocation: room ID of the room this thing should be placed in at the beginning of the game
    :type initlocation: string
    """

    def __init__(self, description, name, ID="", takable=True, value=0, key=None, initlocation=""):
        self.description = description
        self.name = name    # thing will be called like this in the game
        self.id = ID if ID else name    # key in world.items, must be unique
        self.takable = takable
        self.value = value
        # this can be used for items that need to fit somewhere
        self.key = key
        # room id to put the item at game start
        self.initlocation = initlocation


    def describe(self):
        """return the description
        """
        return self.description


class Weapon(Item):

    def __init__(self, *args, **kwargs):
        Item.__init__(self, *args, **kwargs)


class Monster(Item):
    """
    monsters or people, can fight, get spawned or always be at one place, get killed

    :param deaddescript: string describing the thing when it's dead
    :param strength: float between 0 and 1
    :param spawns_in: list of strings with room IDs (or even only part of room IDs) that specify in which rooms the monster should spawn
    :param spawns_at: define the daytime at which the monster should spawn (always/night/day)
    :param spawn_prob: probability to spawn (float between 0 and 1)
    :param ignoretext: this gets returned by :func:`textgame.player.Player.attack` if the monster's history is -1. This only happens if the monster has an initlocation
    :param status: dict that can (but doesn't need to) contain the following key-value pairs (values must be bool): 'alive', 'active', 'fighting', 'trap', 'singleencounter', 'harmless'
    """

    def __init__(self, description, name, ID="", takable=False,\
                 deaddescript="", initlocation="", strength=0,\
                 spawns_in=None, spawns_at="always", spawn_prob=0,\
                 ignoretext="", status=None):

        Item.__init__(self, description, name, ID=ID, takable=takable, initlocation=initlocation)

        # description of the thing when it's dead
        self.deaddescript = deaddescript
        self.strength = strength    # how hard will it be to kill ([0..1])
        # rooms in which monster should be spawned randomly (may only be part of room.id)
        self.spawns_in = spawns_in if spawns_in else []
        # time to spawn
        self.spawns_at = spawns_at
        # probability to spawn ([0,1])
        self.spawn_prob = spawn_prob
        self.history = -1   # used to keep track of fights/conversations
        # this is shown if the monster is passive
        self.ignoretext = ignoretext
        self.status = {"alive": True, "active": False, "fighting": False,\
            "trap": False, "singleencounter": False, "harmless": False}
        if status:
            self.status.update(status)


    def kill(self):
        """
        set ``description`` to ``deaddescript`` and make sure this monster does not
        spawn anymore
        """
        self.status["alive"] = False
        self.description = self.deaddescript
        self.spawn_prob = 0
