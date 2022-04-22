Items
========

Adding items to your world works in a similar way like adding rooms. All you have to do is define their properties in a file called ``items.yml`` inside the resources folder:

.. code-block:: yaml

    diamond:  # unique identifyer
        name: sparkling diamond  # name that is displayed in the inventory
        ID: diamond  # name that is used in-game for interacting
        value: 12
        initlocation: field_0

    boulder:
        description: A large boulder lies on the ground.
        name: boulder
        value: 0
        initlocation: field_1
        takable: false

That's it! No need to add code. Let's see how this looks in-game:

.. code-block::

    $ python main.py
    → look
    You are in a wide rocky pit. An aisle leads upwards to the north.
    A sparkling diamond lies around!

    → take diamond
    You carry now a sparkling diamond.
    
    → n
    You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. A slippery aisle leads downwards to the south.
    A large boulder lies on the ground.

    → take boulder
    You can't take that.

    → drop diamond
    Dropped.

    → look
    You are standing in the middle of a wide open field. In the west the silhouette of an enormeous castle cuts the sky. A slippery aisle leads downwards to the south.
    A large boulder lies on the ground.
    A sparkling diamond lies around!
