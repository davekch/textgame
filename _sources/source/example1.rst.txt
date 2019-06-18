First steps
==================

This example shows how to setup a basic text adventure game.

First, import the relevant classes and set up a logger

.. code-block:: python

   from textgame.player import Player
   from textgame.parser import Parser
   from textgame.world import World
   import logging
   logging.basicConfig(level=logging.WARNING, format='%(levelname)-8s %(name)-16s %(funcName)-18s: %(message)s')

Next, we define some rooms and items. For further explanation of these dicts, see the documentation of :class:`textgame.room.Room`.

.. code-block:: python

   myrooms = {
    "field_0": {
        "descript": "You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. North of you is a birch grove. A dark forest reaches to the east.",
        "sdescript": "You are in a wide open field.",
        "value": 0,
        "doors": {"north": "field_2", "south": "field_1"}
    },
    "field_1": {
        "descript": "You are in a wide rocky pit. An aisle leads upwards to the north.",
        "sdescript": "You're in the rocky pit.",
        "errors": {
            "south": "The slope is too steep here."
        },
        "doors": {"north": "field_0", "up": "field_0"},
        "dir_descriptions": {"up": "You spread your wings and start to fly."},
        "locked": {"north":{"closed":True, "key":123}},
        "hint": "here's my special hint for you.",
        "hint_value": 7
    },
    "field_2": {
        "descript": "You are in a clear birch grove. A small stream flows by.",
        "sdescript": "You are in the birch grove.",
        "dark": {"always": True, "now": True},
        "sound": "You hear the sound of water splashing.",
        "doors": {"south": "field_0"}
    }
   }

   # add some items
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


Now we can setup a world, player and parser:

.. code-block:: python

   world = World(rooms=myrooms, items=myitems)
   player = Player(world, world.room("field_0"))
   parser = Parser(player)

Finally a possible game routine could be

.. code-block:: python

   while player.status["alive"]:
        response = parser.understand( input("> ") )
        print(response)
