Creating a custom player
============================

The default :class:`textgame.player.Player` can do a bunch of basic activities but nothing too exciting. In this tutorial, we will create a custom Player class with some additional functionality.

Say we want our player to be able to do some magic by giving the command "wave wand". Add the class ``MyPlayer`` to our main program:

.. code-block:: python

    # main.py

    from textgame.player import Player, register

    class MyPlayer(Player):

        # map this method to the command "wave"
        @register("wave")
        def do_magic(self, noun):
            # what should happen if the user just types "wave"?
            if not noun:
                return "What?"
            # what if the item the user wants to use is not in our inventory?
            if noun not in self.inventory:
                return "You don't have it!"
            if noun == "wand":
                return "Blue sparks fly through the air! Magic!"
            # what if the user tries to wave something other than a wand?
            else:
                return "I don't know how to wave a {}".format(noun)

    # ...
    # change the line where player is instantiated
    player = MyPlayer(world, world.room("field_0"))


Let's break the code down a bit:

* ``MyPlayer`` inherits from ``Player`` so we don't have to reimplement the basics
* additional functionality gets implemented as methods of the custom Player class
* methods can be mapped to commands by decorating them with :func:`textgame.player.register` (methods which are decorated like that can be collected with :func:`textgame.player.Player.get_registered_methods`, like we did in the first part of the tutorial)
* methods which are decorated like that should take a string as an argument. This string will be the noun in a user command like "verb noun"
* Player methods handle the different cases of nouns that can be used with the activity
* Player methods must *always* return a string (or a :class:`textgame.parser.EnterYesNoLoop`, more on that later)

The only thing still missing is a wand. Let's add it to our items:

.. code-block:: yaml

    wand:
        description: A wand lies around.
        name: wand
        value: 0
        initlocation: field_1

That's how this looks like in the game:

.. code-block::

    → wave
    What?

    → wave wand
    You don't have it!

    → take wand
    You carry now a wand.

    → wave wand
    Blue sparks fly through the air! Magic!

So far, the magic is quite underwhelming. I want the command "wave wand" to transport the player from ``field_1`` to a new hidden place and back, but *only* if the player is a magician. They can become a magician by waving the wand once. Attributes like being a magician can be stored inside the player's ``status`` dict. It also contains values for ``alive``, ``fighting`` and ``trapped``.

Here is a possible implementation:

.. code-block:: python

    @register("wave")
    def do_magic(self, noun):
        # what should happen if the user just types "wave"?
        if not noun:
            return "What?"
        # what if the item the user wants to use is not in our inventory?
        if noun not in self.inventory:
            return "You don't have it!"
        if noun == "wand":
            if not self.status.get("magician"):
                self.status["magician"] = True
                return "Wowzers, you are now a magician!"
            # check where the player is waving the wand
            if self.location.id in ["field_1", "hidden_place"]:
                # relocate the player
                if self.location.id == "field_1":
                    self.location = self.world.room("hidden_place")
                else:
                    self.location = self.world.room("field_1")
                # add the room's value to the score
                if not self.location.visited:
                    self.score += self.location.visit()
                # construct a message for display
                msg = "You fly through the air!\n"
                msg += self.look()  # describe the new room
                return msg
            else:
                return "Blue sparks fly through the air! Magic!"
        # what if the user tries to wave something other than a wand?
        else:
            return "I don't know how to wave a {}".format(noun)


A few things to note here:

* The ID of the current room can be accessed via ``self.location.id``. ``self.location`` is an object of type :class:`textgame.room.Room`. A player also has ``self.oldlocation`` where the previous room is stored.
* Other rooms can be obtained with ``self.world.room(room_id)``.
* :class:`textgame.room.Room` objects have a ``visited`` property, stating if the player has already been there. If your player can go to a location by custom means (not with the "go"-command), remember to mark the location as visited by calling :func:`textgame.room.Room.visit`. This method marks the room as visited and returns the value of the room, so you can add it to the player's score.

I'll leave it to you to add a ``hidden_place`` to your rooms. Waving a wand in the game now looks like this:

.. code-block::

    You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. A slippery aisle leads downwards to the south.
    A large boulder lies on the ground.
    A wand lies around.

    → take wand
    You carry now a wand.

    → wave wand
    Wowzers, you are now a magician!

    → wave wand
    You fly through the air!
    You are in a secret room! Magic skribblings decorate the walls.

    → wave wand
    You fly through the air!
    You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. A slippery aisle leads downwards to the south.
    A large boulder lies on the ground.

    → go south
    You are in a wide rocky pit. An aisle leads upwards to the north.
    A sparkling diamond lies around!

    → wave wand
    Blue sparks fly through the air! Magic!
