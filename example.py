import textgame

# the module makes use of logging, I recommend using it
# the logger will warn you for example if the rooms / ActionMapper are inconsistent
import logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)-8s %(name)-16s %(funcName)-18s: %(message)s')


# describe some basic rooms
myrooms = {
    "field_0": {
        # long description
        "descript": "You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. North of you is a birch grove. A dark forest reaches to the east.",
        # short description, will be printed if the player has already been here
        "sdescript": "You are in a wide open field.",
        # how much the player's score will increase when this room is first visited
        "value": 0,
        # connections to other rooms
        "doors": {"north": "field_2", "south": "field_1"}
    },
    "field_1": {
        "descript": "You are in a wide rocky pit. An aisle leads upwards to the north.",
        "sdescript": "You're in the rocky pit.",
        # these messages will be printed if the player tries to go in the corresponding direction
        "errors": {
            "south": "The slope is too steep here.",
            "west": "The slope is too steep here.",
            "east": "The slope is too steep here."
        },
        "doors": {"north": "field_0", "up": "field_0"},
        # this will only be printed if the player leaves this room in the given direction
        "dir_descriptions": {"up": "You spread your wings and start to fly."},
        "locked": {"north":{"closed":True, "key":123}},
        "hint": "here's my special hint for you.",
        "hint_value": 7
    },
    "field_2": {
        "descript": "You are in a clear birch grove. A small stream flows by.",
        "sdescript": "You are in the birch grove.",
        # does the player need a source of light to be able to see?
        "dark": {"always": True, "now": True},
        # this will be printed if the player types "listen"
        "sound": "You hear the sound of water splashing.",
        "doors": {"south": "field_0"}
    }
}

# add a random item to field_1
myitems = {
    "key": {
        "description": "A key lies around.",
        "name": "key",
        "key": 123,
        "initlocation": "field_0"
    },
    "diamond": {
        "description": "A sparkling diamond lies around!",
        "name": "diamond",
        "initlocation": "field_1"
    }
}

# add a basic monster that spawns randomly
mymonsters = {
    "wolf": {
        "name": "wolf",
        "description": "A wolf runs towards you!",
        "deaddescript": "A dead wolf lies on the ground.",
        # define a list of rooms/room types in which this monster should spawn
        "spawns_in": ["field"],
        # define a time at which monster should spawn (day/night/always)
        "spawns_at": "always",
        "spawn_prob": 0,
        "strength": 0.3
    }
}


# create a subclass of Player and add some functionality
class MyPlayer(textgame.player.Player):

    def __init__(self, world, initlocation):
        textgame.player.Player.__init__(self, world, initlocation)

    @textgame.player.action_method
    def scream(self):
        return "AAAAAAAAAHHH!!!"


# create mapping between input and our new method
class MyParser(textgame.parser.Parser):

    def __init__(self, player):
        textgame.parser.Parser.__init__(self, player)

        # first, we map the inputs "scream" and "shout" both to the word "scream"
        self.legal_verbs.update({
            "scream": "scream",
            "shout": "scream"
        })
        # now we map the word "scream" to our method
        self.actionmap.update({
            "scream": player.scream
        })


# create the world based on our rooms and items
world = textgame.world.World(rooms=myrooms, items=myitems, monsters=mymonsters)
# create instance of MyPlayer
player = MyPlayer(world, world.room("field_0"))

# create a parser
parser = MyParser(player)


# start the game routine
while player.status["alive"]:
    command = input("> ")
    response = parser.understand(command)
    print(response)
    print()
