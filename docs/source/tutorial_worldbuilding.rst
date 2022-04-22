Two rooms and first steps
===========================

First, let's setup a new folder which will contain our project.

.. code-block:: bash

    mkdir mygame
    cd mygame

Now, we're ready to build a first room! The most convenient way to do this with textgame is to define the properties of every room in a file that can be parsed into a python dictionary.
I chose YAML (``pip install pyyaml``) for this tutorial, because it's very human readable but you're free to use something else, like JSON or TOML.

Create a new folder and put the file ``rooms.yml`` inside it:

.. code-block:: bash

    mkdir resources
    touch rooms.yml

Put the following into ``rooms.yml``:

.. code-block:: yaml

    field_0:  # some unique identifyer for the room
        # long description
        descript: You are in a wide rocky pit. An aisle leads upwards to the north.
        # short description, will be printed if the player has already been here
        sdescript: You're in the rocky pit.
        # how much the player's score will increase when this room is first visited
        value: 0
        # these messages will be printed if the player tries to go in the corresponding direction
        errors:
            south: The slope is too steep here.
            east: The slope is too steep here.
        hint: here's my special hint for you.
        hint_value: 7

Now that we have a world with a single room to hang out in, we can finally write some code to try it out. Create a file in the ``mygame`` directory called ``main.py`` and put the following content in it:

.. code-block:: python

    from textgame.world import World
    import yaml

    world = World()
    world.load_resources("resources", loader=yaml.safe_load)


In order to walk around in this world, we need to create a :class:`textgame.player.Player` and a :class:`textgame.parser.Parser`. The parser makes sense of the user's input. Because textgame's default player can already do quite a lot, we don't need to do anything other than initialize it and link its methods to the parser.
Extend ``main.py`` by the following lines:

.. code-block:: python

    from textgame.parser import Parser
    from textgame.player import Player

    # ...

    # create a player and place it in the first room
    player = Player(world, world.room("field_0"))
    parser = Parser()
    # link player methods to commands
    parser.set_actionmap(player.get_registered_methods())

Now the only thing that's missing is a game-loop to ask the user for input, process it and print the result to the screen. :class:`textgame.game.Game` makes this easy enough:

.. code-block:: python

    from textgame.game import Game

    # ...

    # put everything together
    game = Game(player, parser)

    if __name__ == "__main__":
        while not game.over():
            command = input("→ ")
            reply = game.play(command)
            print(reply)

Ready to go!

.. code-block::

    $ python main.py
    → look
    You are in a wide rocky pit. An aisle leads upwards to the north.

    → go north
    You can't go in this direction.

    → go south
    The slope is too steep here.

    → take treasure
    I see no treasure here.

    → take aisle
    You can't take that.

    → hint
    I have a hint for you, but it will cost you 7 points. Do you want to hear it?

    → yes
    here's my special hint for you.

    → score
    Your score is -7.

Impressed yet? There are several noteworthy features:

- You can look around to get the description of the room.
- When trying to go south, the reply is not the generic "You can't go there" but the message that we specified in the ``errors`` dictionary for this room.
- When trying to take something, the reply is different when the noun appears in the description of the room (you can't take an aisle and there is no treasure).
- You can ask for a hint, refuse or accept it and get the hint that we defined for this room.
- You can check your score.

A world consisting of only one room is pretty boring, so let's create another one. The description of the first room says "An aisle leads upwards to the north." so I'm going to connect the second room to the north (and up) of the first one:

.. code-block:: yaml

    field_0:
        # ...
        doors: {"north": "field_1", "up": "field_1"}
        # this will only be printed if the player leaves this room in the given direction
        dir_descriptions: {"up": "You spread your wings and start to fly."}

    field_1:
        descript: You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. A slippery aisle leads downwards to the south.
        sdescript: You are in a wide open field.
        doors: {"south": "field_0", "down": "field_0"}

Note how I had to define the connection between the two rooms in both directions: Field_0 has a door to the north leading to field_1 and field_1 has a door to the south leading to field_0.
This gives you the possibility to be arbitrarily mean to your users: you can build "warped" connections where the player goes south but has to go east go get back. You can even create connections that go only one way.

I've also added ``dir_descriptions`` to field_0. Look for yourself what it does:

.. code-block::

    $ python main.py
    → go north
    You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. A slippery aisle leads downwards to the south.

    → go south
    You are in a wide rocky pit. An aisle leads upwards to the north.

    → go up
    You spread your wings and start to fly.
    You are in a wide open field.

    → go back
    You're in the rocky pit.

    → up
    You spread your wings and start to fly.
    You are in a wide open field.

I used two new features here (besides the movement):

- "go back": this brings the user to the last visited location, given that there is a direct connection to it.
- abbreviations: instead of writing "go up", users can just write "up" or even just "u"; same for all the other directions north, south, east, west and down.

A complete list of valid keywords you can use to define a room can be found in the documentation of :meth:`textgame.room.Room.fill_info`.

That's our world for now. Next, let's put some items in it.
