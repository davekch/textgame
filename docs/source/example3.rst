Time dependent events
======================

Everything that should happen at a specific time or after a time interval ('time' meaning steps in the game here) should probably go into :func:`textgame.world.World.update`.

Eg there's a 'dude' in 'room_42' that disappears after 47 steps into the game and comes back after another 13 steps:

.. code-block:: python

   from textgame.world import World

   class MyWorld(World):

        def update(self, player):

            if self.time == 47:
                # move the dude to the storage room
                self.storage_room.add_monster(
                    self.room("room_42").monsters.pop("dude")
                )
            elif self.time == 60:
                # move him back
                self.room("rooms").add_monster(
                    self.storage_room.monsters.pop("dude")
                )

            # continue as usual
            return World.update(self, player)
