import logging
logger = logging.getLogger("textgame.movable")
logger.addHandler(logging.NullHandler())


class Item:
    """
    everything that is somewhat movable like treasures, weapons, tools, monsters
    """

    def __init__(self, description, name, ID="", takable=True, value=0, initlocation=""):
        self.description = description
        self.name = name    # thing will be called like this in the game
        self.id = ID if ID else name    # key in world.items, must be unique
        self.takable = takable
        self.value = value
        # room id to put the item at game start
        self.initlocation = initlocation


    def describe(self):
        return self.description


class Weapon(Item):
    """
    anything that is used in a fight
    """

    def __init__(self, *args, **kwargs):
        Item.__init__(self, *args, **kwargs)


class Monster(Item):
    """
    monsters or people, can get fight, get spawned or always be at one place, get killed
    """

    def __init__(self, description, name, ID="", takable=False,\
                 deaddescript="", initlocation="", strength=0,\
                 spawns_in=None, spawns_at="always", spawn_prob=0,\
                 safe_kill=None, ignoretext="", status=None):

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
        self.status["alive"] = False
        self.description = self.deaddescript
        self.spawn_prob = 0
