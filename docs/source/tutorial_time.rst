Timed events
==============

This tutorial will be about altering the world's state if certain conditions are met, independent of what the user is currently doing.
The first example will be about events happening at a defined time into the game and the second example will be about events happening at a defined time relative to a user action.
"Time" in this library means number of moves.

After every user command, the function :func:`textgame.world.World.update` gets called. It handles time, daytime and spawning of monsters.

.. note::

    If you don't want the update function to be called after a command, you can prevent that by decorating the corresponding method with :func:`textgame.player.timeless`.

To define our own events, we need to override the ``update`` method:

.. code-block:: python

    # main.py

    class MyWorld(World):

        def update(self, player):
            msg = World.update(self, player)
            return msg


    world = MyWorld()

So far, our custom ``World`` class does nothing new.


Absolute time
--------------
Let's make a grail appear out of nowhere in the 42th move (don't forget to add a ``grail`` to ``items.yml``!):

.. code-block:: python

    def update(self, player):
        msg = World.update(self, player)
        if self.time == 42:
            grail = self.storage_room.get_item("grail")
            player.location.add_item(grail)
            msg += "\nA golden grail appears out of nowhere!"

        return msg


Relative time
----------------
