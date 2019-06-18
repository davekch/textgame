Adding functionality to Player
==============================

Add a simple method to Player
--------------------------------

You can define custom methods by writing your own class that inherits from :class:`textgame.player.Player`. Say you want your player to eat something:

.. code-block:: python

   from textgame.player import Player, action_method

   class MyPlayer(Player):

        @action_method
        def eat(self, noun):
            # check if player carries noun
            if noun in self.inventory:
                # define behaviour for different nouns
                if noun == "lunch":
                    # remove it
                    self.inventory.pop("lunch")
                    return "That was delicious!"
                return "Ew!"
            return "You don't have it!"


If you want user input like 'eat lunch' to call this method like ``player.eat("lunch")``, you need to tell the parser to do so.

.. code-block:: python

   from textgame.parser import Parser

   # use the world from previous example
   player = MyPlayer(world, world.room("field_0"))
   parser = Parser(player)

   # tell the parser it's ok to say 'eat'
   parser.legal_verbs.update({
    "eat": "eat"
   })
   # map the new verb to the method
   parser.actionmap.update({
    "eat": player.eat
   })


Overwrite an existing player method
-------------------------------------

In principle overwriting methods is straight forward, however you need to be careful with the decorator :func:`textgame.player.action_method`. It makes sure that :func:`textgame.world.World.update` gets called at the end of the method.
However, you don't want to call it twice in case your new method makes use of the old one, so you need to call the old one undecorated. Observe:
Say you want to add an item's value to the player's score if he/she takes it.

.. code-block:: python

   class MyPlayer(Player):

       @action_method
       def take(self, itemid):
            # check if the thing is here
            if itemid in self.location.items:
                self.score += self.location.items[itemid].value

            # now we call take, but without the action_method-decorator
            return Player.take.undecorated(self, itemid)


Trigger a yes/no conversation and magic words
---------------------------------------------

Here's an obscure example of a magic word that takes the player to a magic room, but only if he/she owns a coin and confirms.

.. code-block:: python

   from textgame.Parser import EnterYesNoLoop

   class MyPlayer(Player):

       @action_method
       def magicword(self):
            if "coin" in self.inventory:

                # define a helper function that gets called if the player answers yes
                def magicmove():
                    self.location = self.world.room("magicroom")
                    msg += self.location.check_restrictions(self)
                    msg += self.location.describe()
                    if not self.location.visited:
                        self.score += self.location.visit()
                    return msg

                return EnterYesNoLoop(
                    question = "Do you really want to travel magically?",
                    yes = magicmove,
                    no = "You stay where you are.")

            # do nothing if there's no coin
            return "Nothing happens."

Again, you need to map a word to this method.


Unlock advanced modes for Player
---------------------------------

If you want certain methods to work only if the player did something special before, you can do so by dynamically adding attributes to the player:

.. code-block:: python

   class MyPlayer(Player):

        @action_method
        def prerequisite(self, noun):
            # make this player a magician
            self.magician = True
            # ....

        @action_method
        def do_magic(self, noun):
            # check if this player is a magician
            if hasattr(self, "magician"):
                # ...
            else:
                return "You can't do this yet!"
