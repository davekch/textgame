NPCs and confirmation dialogs
===============================

NPCs
------------

So far the player is the only creature roaming our world. In this tutorial we will add a NPC (non-player character) who deals with wooden bows.

The Textgame library provides the :class:`textgame.movable.Monster` for a basic implementation of NPCs. Monsters / NPCs are stored in their location's ``monsters`` attribute. To define one, all we need to do is to create a file ``monsters.yml`` inside the ``resources`` folder and fill it with some descriptive information about our monster:

.. code-block:: yaml

    # resources/monsters.yml
    dealer:  # unique ID
        description: A dealer stands in his booth with a fine collection of wooden bows.
        name: dealer
        initlocation: marketplace  # the ID of the room where the dealer is located

Let's also quickly add the marketplace and define the bow:

.. code-block:: yaml

    # resources/rooms.yml
    field_0:
        # ...
        doors: {"north": "field_1", "up": "field_1", "west": "marketplace"}

    marketplace:
        descript: You are at the marketplace in the middle of a small village.
        sdescript: You are at the marketplace.
        doors: {"east": "field_0"}

    # resources/items.yml
    bow:
        description: A wooden bow lies on the ground.
        name: bow
        value: 12
        initlocation: storage_room

Now I want the player to be able to interact with the dealer. For example, the player could trade something of value for a bow. The bow-item is not visible to the user from the beginning and the traded item will vanish from the world after the trade. Items like that can be placed in a predefined room with ID ``storage_room`` (accessible like every room with ``world.room("storage_room")`` or via the shortcut ``world.storage_room``).

The trade command should do the following:

* check if the item the user wants to trade is in the player's inventory
* check if there is a dealer
* check if the dealer still has bows
* compare the value of the player's item and the dealer's good (in our case the bow)
* if the value is enough, replace the traded item with the bow

.. code-block:: python

    # main.py in class MyPlayer ...

    @register("trade")
    def trade(self, noun):
        if not noun:
            return "Trade what?"
        if noun not in self.inventory:
            return f"You don't have a {noun}"
        # check if (or which) the dealer is present
        if "dealer" in self.location.monsters:
            # check if the bow is still available
            if not "bow" in self.world.storage_room.items:
                return "Apparently the dealer ran out of bows!"
            # get the bow from the storage room and remove it from there
            bow = self.world.storage_room.pop_item("bow")
            # compare values
            if self.inventory[noun].value >= bow.value:
                # remove noun-item from player's inventory
                thing = self.inventory.pop(noun)
                # put it inside the storage room (optional)
                self.world.storage_room.add_item(thing)
                # add bow to inventory
                self.inventory["bow"] = bow
                return f"You traded your {noun} for a wooden bow."
            else:
                # return the bow to the storage room
                self.world.storage_room.add_item(bow)
                return f"Your {noun} is not valuable enough!"
        else:
            return f"There is no one to trade your {noun} with."

This already introduces some pretty interesting interactions to the game:

.. code-block::

    You are at the marketplace in the middle of a small village.
    A dealer stands in his booth with a fine collection of wooden bows.

    → inventory
    You are now carrying:
     A sparkling diamond
     A wand

    → trade wand
    Your wand is not valuable enough!

    → trade diamond
    You traded your diamond for a wooden bow.

    → inventory
    You are now carrying:
     A wand
     A bow


Confirmation Dialogs
----------------------

To be able to trade is nice, but to the user one thing might seem unfair: They can't know which items are valuable enough and just have to try. If it works, the trade is immediately carried out without the user being able to cancel.
For this case, a player method can return a :class:`textgame.parser.EnterYesNoLoop` instead of a string.

If an ``EnterYesNoLoop`` is returned by a player method, the parser falls into a mode where it only accepts "yes" or "no" as commands. On creation of an ``EnterYesNoLoop`` a question (string), a yes-case (string or function with no arguments) and a no-case (string or function with no arguments) has to be defined.

In our case, we want the trade only to happen if the user agrees to the deal. The part after ``if self.inventory[noun].value >= bow.value:`` in the code-snippet above should be executed if the user types "yes", otherwise the trade is cancelled.

.. code-block:: python

    if self.inventory[noun].value >= bow.value:
        # move the actual trade inside a helper function
        def trade_bow():
            # remove noun-item from player's inventory
            thing = self.inventory.pop(noun)
            # put it inside the storage room (optional)
            self.world.storage_room.add_item(thing)
            # add bow to inventory and remove it from storage room
            self.inventory["bow"] = self.world.storage_room.pop_item("bow")
            return f"You traded your {noun} for a wooden bow."
            
        return EnterYesNoLoop(
            question=f"Do you want to trade your {noun} for a wooden bow?",
            yes=trade_bow,
            no=f"Ok, keep your {noun} then."
        )

Now the user can cancel or accept a trade:

.. code-block::

    → trade diamond
    Do you want to trade your diamond for a wooden bow?

    → no
    Ok, keep your diamond then.

    → trade diamond
    Do you want to trade your diamond for a wooden bow?

    → yes
    You traded your diamond for a wooden bow.

    → inventory
    You are now carrying:
     A bow
